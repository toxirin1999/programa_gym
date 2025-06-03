from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    PerfilGamificacion, Logro, Quest, LogroUsuario, 
    QuestUsuario, HistorialPuntos, Nivel
)
from entrenos.models import EntrenoRealizado, SerieRealizada
from rutinas.models import Ejercicio

logger = logging.getLogger(__name__)

class GamificacionService:
    """
    Servicio para gestionar la lógica de gamificación, cálculo de puntos,
    verificación de logros y misiones.
    """
    
    @classmethod
    def procesar_entreno(cls, entreno):
        """
        Procesa un entrenamiento completado, calculando puntos y verificando logros.
        
        Args:
            entreno: Objeto EntrenoRealizado
        
        Returns:
            dict: Resultados del procesamiento (puntos, logros, misiones)
        """
        if not entreno or not entreno.cliente:
            logger.error("Entrenamiento inválido o sin cliente asociado")
            return None
            
        # Obtener o crear perfil de gamificación
        perfil, created = PerfilGamificacion.objects.get_or_create(
            cliente=entreno.cliente,
            defaults={
                'nivel_actual': Nivel.objects.filter(numero=1).first()
            }
        )
        
        # Calcular puntos del entrenamiento
        puntos = cls.calcular_puntos_entreno(entreno)
        
        # Registrar puntos en el historial
        historial = HistorialPuntos.objects.create(
            perfil=perfil,
            puntos=puntos,
            entreno=entreno,
            descripcion=f"Entrenamiento: {entreno.rutina.nombre if entreno.rutina else 'Personalizado'}"
        )
        
        # Actualizar estadísticas del perfil
        cls.actualizar_estadisticas_perfil(perfil, entreno)
        
        # Verificar logros
        logros_desbloqueados = cls.verificar_logros(perfil, entreno)
        
        # Verificar misiones
        misiones_completadas = cls.verificar_misiones(perfil, entreno)
        
        # Actualizar nivel del usuario
        subio_nivel = perfil.actualizar_nivel()
        
        return {
            'puntos': puntos,
            'puntos_totales': perfil.puntos_totales,
            'logros_desbloqueados': logros_desbloqueados,
            'misiones_completadas': misiones_completadas,
            'subio_nivel': subio_nivel,
            'nivel_actual': perfil.nivel_actual
        }
    
    @classmethod
    def calcular_puntos_entreno(cls, entreno):
        """
        Calcula los puntos ganados por un entrenamiento según las series realizadas.
        
        Args:
            entreno: Objeto EntrenoRealizado
        
        Returns:
            int: Puntos ganados
        """
        puntos_totales = 0
        
        # Obtener todas las series del entrenamiento
        series = SerieRealizada.objects.filter(entreno=entreno)
        
        for serie in series:
            if not serie.completado:
                continue
                
            # Fórmula base: Peso × Repeticiones × Coeficiente
            puntos_serie = serie.peso_kg * serie.repeticiones
            
            # Aplicar coeficiente según tipo de ejercicio
            if serie.ejercicio:
                # Coeficientes por tipo de ejercicio
                if serie.ejercicio.grupo_muscular in ['Piernas', 'Espalda']:
                    # Ejercicios compuestos grandes
                    coeficiente = 1.5
                elif serie.ejercicio.grupo_muscular in ['Pecho', 'Hombros']:
                    # Ejercicios compuestos medianos
                    coeficiente = 1.2
                else:
                    # Ejercicios de aislamiento
                    coeficiente = 1.0
                    
                puntos_serie *= coeficiente
            
            puntos_totales += round(puntos_serie)
        
        # Bonificación por entrenamiento completo
        if series.count() > 0 and series.filter(completado=True).count() == series.count():
            puntos_totales += 50  # Bonus por completar todas las series
        
        return puntos_totales
    
    @classmethod
    def actualizar_estadisticas_perfil(cls, perfil, entreno):
        """
        Actualiza las estadísticas del perfil de gamificación tras un entrenamiento.
        
        Args:
            perfil: Objeto PerfilGamificacion
            entreno: Objeto EntrenoRealizado
        """
        # Actualizar puntos totales
        puntos_entreno = cls.calcular_puntos_entreno(entreno)
        perfil.puntos_totales += puntos_entreno
        
        # Actualizar contador de entrenamientos
        perfil.entrenos_totales += 1
        
        # Actualizar racha de entrenamientos
        fecha_actual = timezone.now().date()
        
        if perfil.fecha_ultimo_entreno:
            dias_diferencia = (fecha_actual - perfil.fecha_ultimo_entreno.date()).days
            
            if dias_diferencia == 1:
                # Entrenamiento en día consecutivo
                perfil.racha_actual += 1
                perfil.racha_maxima = max(perfil.racha_actual, perfil.racha_maxima)
            elif dias_diferencia > 1:
                # Se rompió la racha
                perfil.racha_actual = 1
            # Si es el mismo día, no afecta la racha
        else:
            # Primer entrenamiento
            perfil.racha_actual = 1
            perfil.racha_maxima = 1
        
        perfil.fecha_ultimo_entreno = entreno.fecha
        perfil.save()
    
    @classmethod
    def verificar_logros(cls, perfil, entreno=None):
        """
        Verifica y actualiza los logros del usuario.
        
        Args:
            perfil: Objeto PerfilGamificacion
            entreno: Objeto EntrenoRealizado (opcional)
            
        Returns:
            list: Logros desbloqueados
        """
        logros_desbloqueados = []
        
        # Obtener todos los logros disponibles
        logros = Logro.objects.all()
        
        for logro in logros:
            # Verificar si ya está completado
            logro_usuario, created = LogroUsuario.objects.get_or_create(
                perfil=perfil,
                logro=logro,
                defaults={'progreso_actual': 0, 'completado': False}
            )
            
            if logro_usuario.completado:
                continue
            
            # Verificar progreso según tipo de logro
            progreso_actualizado = False
            
            # Obtener tipo de logro
            tipo_categoria = logro.tipo.categoria
            
            if tipo_categoria == 'hito':
                progreso_actualizado = cls._verificar_logro_hito(logro_usuario, perfil, entreno)
            elif tipo_categoria == 'consistencia':
                progreso_actualizado = cls._verificar_logro_consistencia(logro_usuario, perfil)
            elif tipo_categoria == 'superacion':
                progreso_actualizado = cls._verificar_logro_superacion(logro_usuario, perfil, entreno)
            elif tipo_categoria == 'especial':
                progreso_actualizado = cls._verificar_logro_especial(logro_usuario, perfil, entreno)
            
            # Verificar si se completó el logro
            if progreso_actualizado and logro_usuario.progreso_actual >= logro.meta_valor and not logro_usuario.completado:
                logro_usuario.completado = True
                logro_usuario.fecha_desbloqueo = timezone.now()
                logro_usuario.save()
                
                # Otorgar puntos por el logro
                if logro.puntos_recompensa > 0:
                    perfil.puntos_totales += logro.puntos_recompensa
                    perfil.save()
                    
                    # Registrar en historial
                    HistorialPuntos.objects.create(
                        perfil=perfil,
                        puntos=logro.puntos_recompensa,
                        logro=logro,
                        descripcion=f"Logro desbloqueado: {logro.nombre}"
                    )
                
                logros_desbloqueados.append(logro)
        
        return logros_desbloqueados
    
    @classmethod
    def _verificar_logro_hito(cls, logro_usuario, perfil, entreno):
        """Verifica logros de tipo 'hito'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        
        # Verificar por nombre o patrón del logro
        if "tonelada" in nombre_logro or "ton" in nombre_logro:
            # Logros de peso total levantado
            peso_total = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                completado=True
            ).aggregate(
                total=Sum(models.F('peso_kg') * models.F('repeticiones'))
            )['total'] or 0
            
            logro_usuario.progreso_actual = int(peso_total)
            logro_usuario.save()
            return True
            
        elif "entreno" in nombre_logro or "entrenamiento" in nombre_logro:
            # Logros de cantidad de entrenamientos
            logro_usuario.progreso_actual = perfil.entrenos_totales
            logro_usuario.save()
            return True
            
        elif "ejercicio" in nombre_logro:
            # Logros de variedad de ejercicios
            ejercicios_unicos = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente
            ).values('ejercicio').distinct().count()
            
            logro_usuario.progreso_actual = ejercicios_unicos
            logro_usuario.save()
            return True
        
        return False
    
    @classmethod
    def _verificar_logro_consistencia(cls, logro_usuario, perfil):
        """Verifica logros de tipo 'consistencia'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        
        if "racha" in nombre_logro or "consecutivo" in nombre_logro:
            # Logros de racha de entrenamientos
            logro_usuario.progreso_actual = perfil.racha_actual
            logro_usuario.save()
            return True
            
        elif "semana" in nombre_logro:
            # Logros de entrenamientos por semana
            fecha_inicio = timezone.now().date() - timedelta(days=7)
            entrenos_semana = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente,
                fecha__gte=fecha_inicio
            ).count()
            
            logro_usuario.progreso_actual = entrenos_semana
            logro_usuario.save()
            return True
            
        elif "mes" in nombre_logro:
            # Logros de entrenamientos por mes
            fecha_inicio = timezone.now().date() - timedelta(days=30)
            entrenos_mes = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente,
                fecha__gte=fecha_inicio
            ).count()
            
            logro_usuario.progreso_actual = entrenos_mes
            logro_usuario.save()
            return True
        
        return False
    
    @classmethod
    def _verificar_logro_superacion(cls, logro_usuario, perfil, entreno):
        """Verifica logros de tipo 'superación'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        
        if entreno and ("récord" in nombre_logro or "record" in nombre_logro or "personal" in nombre_logro):
            # Logros de superar récords personales
            if not hasattr(logro_usuario, 'contador_records'):
                logro_usuario.contador_records = 0
            
            # Verificar si hay nuevos récords en este entrenamiento
            for serie in SerieRealizada.objects.filter(entreno=entreno, completado=True):
                # Buscar el récord anterior para este ejercicio
                mejor_serie_anterior = SerieRealizada.objects.filter(
                    entreno__cliente=perfil.cliente,
                    ejercicio=serie.ejercicio,
                    entreno__fecha__lt=entreno.fecha,
                    completado=True
                ).order_by('-peso_kg').first()
                
                if mejor_serie_anterior and serie.peso_kg > mejor_serie_anterior.peso_kg:
                    logro_usuario.contador_records += 1
            
            logro_usuario.progreso_actual = logro_usuario.contador_records
            logro_usuario.save()
            return True
            
        elif "doble" in nombre_logro or "duplicar" in nombre_logro:
            # Logros de duplicar peso inicial
            if entreno:
                for serie in SerieRealizada.objects.filter(entreno=entreno, completado=True):
                    # Buscar la primera serie registrada para este ejercicio
                    primera_serie = SerieRealizada.objects.filter(
                        entreno__cliente=perfil.cliente,
                        ejercicio=serie.ejercicio,
                        completado=True
                    ).order_by('entreno__fecha').first()
                    
                    if primera_serie and serie.peso_kg >= (primera_serie.peso_kg * 2):
                        logro_usuario.progreso_actual += 1
                        logro_usuario.save()
                        return True
        
        return False
    
    @classmethod
    def _verificar_logro_especial(cls, logro_usuario, perfil, entreno):
        """Verifica logros de tipo 'especial'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        
        if "primer" in nombre_logro:
            # Logro del primer entrenamiento
            if perfil.entrenos_totales >= 1:
                logro_usuario.progreso_actual = 1
                logro_usuario.save()
                return True
                
        elif "perfecto" in nombre_logro:
            # Logro de entrenamiento perfecto (todas las series completadas)
            if entreno:
                series_total = SerieRealizada.objects.filter(entreno=entreno).count()
                series_completadas = SerieRealizada.objects.filter(entreno=entreno, completado=True).count()
                
                if series_total > 0 and series_total == series_completadas:
                    logro_usuario.progreso_actual += 1
                    logro_usuario.save()
                    return True
                    
        elif "cuerpo" in nombre_logro and "completo" in nombre_logro:
            # Logro de entrenar todos los grupos musculares
            if entreno:
                # Obtener grupos musculares entrenados en la última semana
                fecha_inicio = timezone.now().date() - timedelta(days=7)
                grupos_entrenados = SerieRealizada.objects.filter(
                    entreno__cliente=perfil.cliente,
                    entreno__fecha__gte=fecha_inicio,
                    completado=True
                ).values_list('ejercicio__grupo_muscular', flat=True).distinct()
                
                # Obtener total de grupos musculares en el sistema
                todos_grupos = Ejercicio.objects.values_list('grupo_muscular', flat=True).distinct()
                
                # Verificar si se han entrenado todos los grupos
                if set(grupos_entrenados) == set(todos_grupos):
                    logro_usuario.progreso_actual = 1
                    logro_usuario.save()
                    return True
        
        return False
    
    @classmethod
    def verificar_misiones(cls, perfil, entreno=None):
        """
        Verifica y actualiza las misiones del usuario.
        
        Args:
            perfil: Objeto PerfilGamificacion
            entreno: Objeto EntrenoRealizado (opcional)
            
        Returns:
            list: Misiones completadas
        """
        misiones_completadas = []
        
        # Obtener misiones activas
        quests_activas = Quest.objects.filter(activa=True)
        
        # Asignar misiones que el usuario no tenga
        for quest in quests_activas:
            quest_usuario, created = QuestUsuario.objects.get_or_create(
                perfil=perfil,
                quest=quest,
                defaults={
                    'fecha_inicio': timezone.now(),
                    'progreso_actual': 0,
                    'completada': False
                }
            )
            
            # Si ya está completada, continuar con la siguiente
            if quest_usuario.completada:
                continue
            
            # Verificar si la misión ha expirado (para misiones con tiempo limitado)
            if quest.tipo.periodo in ['diaria', 'semanal', 'mensual']:
                dias_duracion = quest.tipo.duracion_dias
                if (timezone.now() - quest_usuario.fecha_inicio).days > dias_duracion:
                    # Reiniciar misión expirada
                    quest_usuario.fecha_inicio = timezone.now()
                    quest_usuario.progreso_actual = 0
                    quest_usuario.save()
            
            # Actualizar progreso según tipo de misión
            progreso_actualizado = False
            
            if quest.tipo.periodo == 'diaria':
                progreso_actualizado = cls._verificar_mision_diaria(quest_usuario, perfil, entreno)
            elif quest.tipo.periodo == 'semanal':
                progreso_actualizado = cls._verificar_mision_semanal(quest_usuario, perfil, entreno)
            elif quest.tipo.periodo == 'mensual':
                progreso_actualizado = cls._verificar_mision_mensual(quest_usuario, perfil, entreno)
            elif quest.tipo.periodo == 'progresiva':
                progreso_actualizado = cls._verificar_mision_progresiva(quest_usuario, perfil, entreno)
            
            # Verificar si se completó la misión
            if progreso_actualizado and quest_usuario.progreso_actual >= quest.meta_valor and not quest_usuario.completada:
                quest_usuario.completada = True
                quest_usuario.fecha_fin = timezone.now()
                quest_usuario.save()
                
                # Otorgar puntos por la misión
                if quest.puntos_recompensa > 0:
                    perfil.puntos_totales += quest.puntos_recompensa
                    perfil.save()
                    
                    # Registrar en historial
                    HistorialPuntos.objects.create(
                        perfil=perfil,
                        puntos=quest.puntos_recompensa,
                        quest=quest,
                        descripcion=f"Misión completada: {quest.nombre}"
                    )
                
                misiones_completadas.append(quest)
                
                # Si es una misión progresiva, activar la siguiente en la serie
                if quest.tipo.periodo == 'progresiva':
                    siguiente_quest = Quest.objects.filter(quest_padre=quest).first()
                    if siguiente_quest:
                        QuestUsuario.objects.get_or_create(
                            perfil=perfil,
                            quest=siguiente_quest,
                            defaults={
                                'fecha_inicio': timezone.now(),
                                'progreso_actual': 0,
                                'completada': False
                            }
                        )
        
        return misiones_completadas
    
    @classmethod
    def _verificar_mision_diaria(cls, quest_usuario, perfil, entreno):
        """Verifica misiones diarias"""
        quest = quest_usuario.quest
        nombre_quest = quest.nombre.lower()
        
        # Verificar si el entrenamiento es de hoy
        if entreno and entreno.fecha.date() == timezone.now().date():
            if "calentamiento" in nombre_quest or "entrenamiento" in nombre_quest:
                # Misión de completar un entrenamiento hoy
                quest_usuario.progreso_actual = 1
                quest_usuario.save()
                return True
                
            elif "superación" in nombre_quest:
                # Misión de superar peso anterior
                for serie in SerieRealizada.objects.filter(entreno=entreno, completado=True):
                    # Buscar la serie anterior para este ejercicio
                    serie_anterior = SerieRealizada.objects.filter(
                        entreno__cliente=perfil.cliente,
                        ejercicio=serie.ejercicio,
                        entreno__fecha__lt=entreno.fecha,
                        completado=True
                    ).order_by('-entreno__fecha').first()
                    
                    if serie_anterior and serie.peso_kg > serie_anterior.peso_kg:
                        quest_usuario.progreso_actual = 1
                        quest_usuario.save()
                        return True
                        
            elif "técnica" in nombre_quest:
                # Misión de completar todas las series programadas
                series_total = SerieRealizada.objects.filter(entreno=entreno).count()
                series_completadas = SerieRealizada.objects.filter(entreno=entreno, completado=True).count()
                
                if series_total > 0 and series_total == series_completadas:
                    quest_usuario.progreso_actual = 1
                    quest_usuario.save()
                    return True
        
        return False
    
    @classmethod
    def _verificar_mision_semanal(cls, quest_usuario, perfil, entreno):
        """Verifica misiones semanales"""
        quest = quest_usuario.quest
        nombre_quest = quest.nombre.lower()
        
        # Definir período semanal desde la fecha de inicio de la misión
        fecha_inicio = quest_usuario.fecha_inicio
        fecha_fin = fecha_inicio + timedelta(days=7)
        
        if "consistencia" in nombre_quest:
            # Misión de completar X entrenamientos esta semana
            entrenos_semana = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente,
                fecha__gte=fecha_inicio,
                fecha__lt=fecha_fin
            ).count()
            
            quest_usuario.progreso_actual = entrenos_semana
            quest_usuario.save()
            return True
            
        elif "cuerpo completo" in nombre_quest:
            # Misión de entrenar todos los grupos musculares
            grupos_entrenados = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio,
                entreno__fecha__lt=fecha_fin,
                completado=True
            ).values_list('ejercicio__grupo_muscular', flat=True).distinct()
            
            # Obtener total de grupos musculares en el sistema
            todos_grupos = Ejercicio.objects.values_list('grupo_muscular', flat=True).distinct()
            
            quest_usuario.progreso_actual = len(set(grupos_entrenados))
            quest_usuario.save()
            return True
            
        elif "variedad" in nombre_quest:
            # Misión de realizar X ejercicios diferentes
            ejercicios_diferentes = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio,
                entreno__fecha__lt=fecha_fin,
                completado=True
            ).values('ejercicio').distinct().count()
            
            quest_usuario.progreso_actual = ejercicios_diferentes
            quest_usuario.save()
            return True
            
        elif "progresión" in nombre_quest:
            # Misión de aumentar peso en X ejercicios
            if entreno and fecha_inicio <= entreno.fecha <= fecha_fin:
                ejercicios_mejorados = set()
                
                for serie in SerieRealizada.objects.filter(entreno=entreno, completado=True):
                    # Buscar la serie anterior para este ejercicio
                    serie_anterior = SerieRealizada.objects.filter(
                        entreno__cliente=perfil.cliente,
                        ejercicio=serie.ejercicio,
                        entreno__fecha__lt=entreno.fecha,
                        entreno__fecha__gte=fecha_inicio,
                        completado=True
                    ).order_by('-entreno__fecha').first()
                    
                    if serie_anterior and serie.peso_kg > serie_anterior.peso_kg:
                        ejercicios_mejorados.add(serie.ejercicio_id)
                
                quest_usuario.progreso_actual = len(ejercicios_mejorados)
                quest_usuario.save()
                return True
        
        return False
    
    @classmethod
    def _verificar_mision_mensual(cls, quest_usuario, perfil, entreno):
        """Verifica misiones mensuales"""
        quest = quest_usuario.quest
        nombre_quest = quest.nombre.lower()
        
        # Definir período mensual desde la fecha de inicio de la misión
        fecha_inicio = quest_usuario.fecha_inicio
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        if "maestría" in nombre_quest:
            # Misión de completar X entrenamientos este mes
            entrenos_mes = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente,
                fecha__gte=fecha_inicio,
                fecha__lt=fecha_fin
            ).count()
            
            quest_usuario.progreso_actual = entrenos_mes
            quest_usuario.save()
            return True
            
        elif "evolución" in nombre_quest:
            # Misión de aumentar volumen total un X% respecto al mes anterior
            # Calcular volumen del mes actual
            volumen_actual = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio,
                entreno__fecha__lt=fecha_fin,
                completado=True
            ).aggregate(
                total=Sum(models.F('peso_kg') * models.F('repeticiones'))
            )['total'] or 0
            
            # Calcular volumen del mes anterior
            fecha_inicio_anterior = fecha_inicio - timedelta(days=30)
            fecha_fin_anterior = fecha_inicio
            
            volumen_anterior = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio_anterior,
                entreno__fecha__lt=fecha_fin_anterior,
                completado=True
            ).aggregate(
                total=Sum(models.F('peso_kg') * models.F('repeticiones'))
            )['total'] or 0
            
            if volumen_anterior > 0:
                porcentaje_aumento = (volumen_actual - volumen_anterior) / volumen_anterior * 100
                quest_usuario.progreso_actual = int(porcentaje_aumento)
                quest_usuario.save()
                return True
            
        elif "explorador" in nombre_quest:
            # Misión de probar X ejercicios nuevos
            # Obtener ejercicios realizados antes del período
            ejercicios_anteriores = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__lt=fecha_inicio
            ).values_list('ejercicio_id', flat=True).distinct()
            
            # Obtener ejercicios realizados durante el período
            ejercicios_actuales = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio,
                entreno__fecha__lt=fecha_fin
            ).values_list('ejercicio_id', flat=True).distinct()
            
            # Contar ejercicios nuevos
            ejercicios_nuevos = set(ejercicios_actuales) - set(ejercicios_anteriores)
            
            quest_usuario.progreso_actual = len(ejercicios_nuevos)
            quest_usuario.save()
            return True
        
        return False
    
    @classmethod
    def _verificar_mision_progresiva(cls, quest_usuario, perfil, entreno):
        """Verifica misiones progresivas"""
        quest = quest_usuario.quest
        
        # Verificar si la misión está asociada a un ejercicio específico
        if quest.ejercicio:
            if "serie" in quest.nombre.lower():
                # Misión de completar X series de un ejercicio
                series_completadas = SerieRealizada.objects.filter(
                    entreno__cliente=perfil.cliente,
                    ejercicio=quest.ejercicio,
                    completado=True
                ).count()
                
                quest_usuario.progreso_actual = series_completadas
                quest_usuario.save()
                return True
                
            elif "kg" in quest.nombre.lower() or "peso" in quest.nombre.lower():
                # Misión de levantar X kg acumulados en un ejercicio
                peso_total = SerieRealizada.objects.filter(
                    entreno__cliente=perfil.cliente,
                    ejercicio=quest.ejercicio,
                    completado=True
                ).aggregate(
                    total=Sum(models.F('peso_kg') * models.F('repeticiones'))
                )['total'] or 0
                
                quest_usuario.progreso_actual = int(peso_total)
                quest_usuario.save()
                return True
                
            elif "corporal" in quest.nombre.lower():
                # Misión de alcanzar X veces el peso corporal en un ejercicio
                if perfil.cliente.peso:
                    # Buscar el máximo peso levantado en el ejercicio
                    max_peso = SerieRealizada.objects.filter(
                        entreno__cliente=perfil.cliente,
                        ejercicio=quest.ejercicio,
                        completado=True
                    ).order_by('-peso_kg').first()
                    
                    if max_peso:
                        ratio = max_peso.peso_kg / perfil.cliente.peso
                        quest_usuario.progreso_actual = int(ratio * 100)  # Guardar como porcentaje
                        quest_usuario.save()
                        return True
        
        # Misiones progresivas generales
        if "entrenamiento" in quest.nombre.lower():
            # Misión de completar X entrenamientos
            quest_usuario.progreso_actual = perfil.entrenos_totales
            quest_usuario.save()
            return True
            
        elif "grupo" in quest.nombre.lower() and "muscular" in quest.nombre.lower():
            # Misión de entrenar X veces un grupo muscular
            if quest.descripcion:
                # Buscar el grupo muscular en la descripción
                for grupo in Ejercicio.objects.values_list('grupo_muscular', flat=True).distinct():
                    if grupo.lower() in quest.descripcion.lower():
                        entrenos_grupo = SerieRealizada.objects.filter(
                            entreno__cliente=perfil.cliente,
                            ejercicio__grupo_muscular=grupo,
                            completado=True
                        ).values('entreno').distinct().count()
                        
                        quest_usuario.progreso_actual = entrenos_grupo
                        quest_usuario.save()
                        return True
        
        return False
