# Archivo: entrenos/gamificacion_service.py
# Servicio de gamificación adaptado al sistema actual del usuario

from django.utils import timezone
from django.db import models
from decimal import Decimal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EntrenamientoGamificacionService:
    """
    Servicio de gamificación adaptado al sistema actual
    """

    @staticmethod
    def procesar_entrenamiento_completado(entreno_realizado):
        """
        Procesa un entrenamiento completado y actualiza la gamificación

        Args:
            entreno_realizado: Instancia del modelo EntrenoRealizado

        Returns:
            dict: Resultado del procesamiento
        """
        try:
            from logros.models import PerfilGamificacion, PruebaUsuario
            from logros.services import GamificacionService

            cliente = entreno_realizado.cliente

            # Obtener o crear perfil de gamificación
            perfil, created = PerfilGamificacion.objects.get_or_create(cliente=cliente)

            if created:
                logger.info(f"Nuevo perfil de gamificación creado para {cliente.nombre}")

            # 1. CALCULAR PUNTOS BASE
            puntos_base = EntrenamientoGamificacionService._calcular_puntos_base(entreno_realizado)

            # 2. VERIFICAR PRUEBAS COMPLETADAS
            pruebas_completadas = EntrenamientoGamificacionService._verificar_pruebas_completadas(
                entreno_realizado, perfil
            )

            # 3. CALCULAR PUNTOS BONUS
            puntos_bonus = EntrenamientoGamificacionService._calcular_puntos_bonus(
                cliente, entreno_realizado
            )

            # 4. SUMAR PUNTOS DE PRUEBAS
            puntos_pruebas = sum(prueba.puntos_recompensa for prueba in pruebas_completadas)

            # 5. CALCULAR TOTAL
            puntos_totales = puntos_base + puntos_bonus + puntos_pruebas

            # 6. ACTUALIZAR PERFIL
            perfil.puntos_totales += puntos_totales
            perfil.save()

            # 7. VERIFICAR ASCENSIÓN
            nivel_anterior = perfil.arquetipo_actual.titulo_arquetipo if perfil.arquetipo_actual else "Ninguno"
            GamificacionService.actualizar_nivel(perfil)
            nivel_nuevo = perfil.arquetipo_actual.titulo_arquetipo if perfil.arquetipo_actual else "Ninguno"

            ascension = nivel_anterior != nivel_nuevo

            # 8. GUARDAR PUNTOS EN ENTRENAMIENTO (si el campo existe)
            if hasattr(entreno_realizado, 'puntos_ganados'):
                entreno_realizado.puntos_ganados = puntos_totales
                entreno_realizado.save(update_fields=['puntos_ganados'])

            logger.info(f"Gamificación procesada para {cliente.nombre}: +{puntos_totales} puntos")

            return {
                'puntos_base': puntos_base,
                'puntos_bonus': puntos_bonus,
                'puntos_pruebas': puntos_pruebas,
                'puntos_totales': puntos_totales,
                'pruebas_completadas': pruebas_completadas,
                'ascension': ascension,
                'nivel_anterior': nivel_anterior,
                'nivel_nuevo': nivel_nuevo,
                'perfil': perfil
            }

        except Exception as e:
            logger.error(f"Error procesando gamificación para entrenamiento {entreno_realizado.id}: {e}")
            return {
                'puntos_totales': 0,
                'pruebas_completadas': [],
                'ascension': False,
                'error': str(e)
            }

    @staticmethod
    def _calcular_puntos_base(entreno_realizado):
        """
        Calcula puntos base por el entrenamiento
        Adaptado al sistema actual del usuario
        """
        puntos = 15  # Puntos base por entrenar

        # Usar el volumen ya calculado en el sistema actual
        volumen_total = float(entreno_realizado.volumen_total_kg or 0)
        puntos_volumen = min(20, int(volumen_total / 200))  # Máximo 20 puntos por volumen

        # Puntos por duración
        duracion = entreno_realizado.duracion_minutos or 60
        puntos_duracion = min(10, int(duracion / 5))  # Máximo 10 puntos por duración

        # Puntos por número de ejercicios
        num_ejercicios = entreno_realizado.numero_ejercicios or 0
        puntos_ejercicios = min(5, num_ejercicios)  # Máximo 5 puntos por ejercicios

        total = puntos + puntos_volumen + puntos_duracion + puntos_ejercicios

        logger.debug(
            f"Puntos base: {puntos} + {puntos_volumen} volumen + {puntos_duracion} duración + {puntos_ejercicios} ejercicios = {total}")

        return total

    @staticmethod
    def _verificar_pruebas_completadas(entreno_realizado, perfil):
        """
        Verifica qué pruebas legendarias se completaron
        Adaptado al modelo EjercicioRealizado del usuario
        """
        from logros.models import PruebaUsuario

        cliente = entreno_realizado.cliente
        pruebas_completadas = []

        if not perfil.arquetipo_actual:
            return pruebas_completadas

        try:
            pruebas_activas = PruebaUsuario.objects.filter(
                cliente=cliente,
                prueba__arquetipo=perfil.arquetipo_actual,
                completada=False
            )

            for prueba_usuario in pruebas_activas:
                prueba = prueba_usuario.prueba

                if EntrenamientoGamificacionService._evaluar_prueba_individual(
                        prueba, cliente, entreno_realizado
                ):
                    # Marcar como completada
                    prueba_usuario.completada = True
                    prueba_usuario.fecha_completada = timezone.now()
                    prueba_usuario.save()

                    pruebas_completadas.append(prueba)
                    logger.info(f"Prueba completada: {prueba.nombre} por {cliente.nombre}")

        except Exception as e:
            logger.error(f"Error verificando pruebas: {e}")

        return pruebas_completadas

    @staticmethod
    def _evaluar_prueba_individual(prueba, cliente, entreno_realizado):
        """
        Evalúa si una prueba específica se completó
        Adaptado al sistema actual del usuario
        """
        clave = prueba.clave_calculo
        meta = prueba.meta_valor

        try:
            if clave == 'primer_entrenamiento':
                return True  # Si llegó aquí, completó un entrenamiento

            elif clave.startswith('press_banca_') and clave.endswith('kg'):
                peso_objetivo = int(clave.replace('press_banca_', '').replace('kg', ''))
                return EntrenamientoGamificacionService._verificar_peso_ejercicio(
                    entreno_realizado, 'press', peso_objetivo
                )

            elif clave.startswith('sentadilla_') and clave.endswith('kg'):
                peso_objetivo = int(clave.replace('sentadilla_', '').replace('kg', ''))
                return EntrenamientoGamificacionService._verificar_peso_ejercicio(
                    entreno_realizado, 'sentadilla', peso_objetivo
                )

            elif clave.startswith('peso_muerto_') and clave.endswith('kg'):
                peso_objetivo = int(clave.replace('peso_muerto_', '').replace('kg', ''))
                return EntrenamientoGamificacionService._verificar_peso_ejercicio(
                    entreno_realizado, 'peso muerto', peso_objetivo
                )

            elif clave == 'volumen_total':
                return EntrenamientoGamificacionService._verificar_volumen_total_historico(cliente, meta)

            elif clave == 'volumen_sesion':
                volumen_sesion = float(entreno_realizado.volumen_total_kg or 0)
                return volumen_sesion >= meta

            elif clave.startswith('racha_') and clave.endswith('_dias'):
                dias_objetivo = int(clave.replace('racha_', '').replace('_dias', ''))
                return EntrenamientoGamificacionService._verificar_racha_dias(cliente, dias_objetivo)

            elif clave == 'entrenos_totales':
                from entrenos.models import EntrenoRealizado
                total_entrenos = EntrenoRealizado.objects.filter(cliente=cliente).count()
                return total_entrenos >= meta

            elif clave == 'record_personal':
                return EntrenamientoGamificacionService._verificar_record_personal(cliente, entreno_realizado)

            else:
                logger.warning(f"Clave de cálculo no reconocida: {clave}")
                return False

        except Exception as e:
            logger.error(f"Error evaluando prueba {prueba.nombre}: {e}")
            return False

    @staticmethod
    def _verificar_peso_ejercicio(entreno_realizado, nombre_ejercicio_buscar, peso_objetivo):
        """
        Verifica si se levantó un peso específico en un ejercicio
        Usa el modelo EjercicioRealizado del usuario
        """
        # Usar el modelo EjercicioRealizado del sistema actual
        ejercicios = entreno_realizado.ejercicios_realizados.filter(
            nombre_ejercicio__icontains=nombre_ejercicio_buscar,
            completado=True
        )

        for ejercicio in ejercicios:
            if ejercicio.peso_kg >= peso_objetivo:
                return True

        return False

    @staticmethod
    def _verificar_volumen_total_historico(cliente, volumen_objetivo):
        """
        Verifica el volumen total acumulado histórico del cliente
        Usa el campo volumen_total_kg del sistema actual
        """
        try:
            from entrenos.models import EntrenoRealizado

            total_volumen = EntrenoRealizado.objects.filter(
                cliente=cliente
            ).aggregate(total=models.Sum('volumen_total_kg'))['total'] or 0

            return float(total_volumen) >= volumen_objetivo

        except Exception as e:
            logger.error(f"Error verificando volumen histórico: {e}")
            return False

    @staticmethod
    def _verificar_racha_dias(cliente, dias_objetivo):
        """
        Verifica si el cliente tiene una racha de días consecutivos entrenando
        Usa el campo fecha del sistema actual
        """
        try:
            from entrenos.models import EntrenoRealizado

            # Obtener entrenamientos ordenados por fecha descendente
            entrenamientos = EntrenoRealizado.objects.filter(
                cliente=cliente
            ).order_by('-fecha')

            if not entrenamientos.exists():
                return False

            # Obtener fechas únicas
            fechas_unicas = []
            for entreno in entrenamientos:
                if entreno.fecha not in fechas_unicas:
                    fechas_unicas.append(entreno.fecha)

            if not fechas_unicas:
                return False

            # Verificar días consecutivos
            racha_actual = 1
            fecha_anterior = fechas_unicas[0]

            for fecha in fechas_unicas[1:]:
                diferencia = (fecha_anterior - fecha).days
                if diferencia == 1:
                    racha_actual += 1
                    fecha_anterior = fecha
                else:
                    break

            return racha_actual >= dias_objetivo

        except Exception as e:
            logger.error(f"Error verificando racha de días: {e}")
            return False

    @staticmethod
    def _verificar_record_personal(cliente, entreno_realizado):
        """
        Verifica si se rompió algún récord personal
        Usa el campo nuevo_record del sistema actual
        """
        try:
            # Verificar si algún ejercicio tiene nuevo_record = True
            records_rotos = entreno_realizado.ejercicios_realizados.filter(
                nuevo_record=True
            ).count()

            return records_rotos > 0

        except Exception as e:
            logger.error(f"Error verificando récords: {e}")
            return False

    @staticmethod
    def _calcular_puntos_bonus(cliente, entreno_realizado):
        """
        Calcula puntos bonus por constancia, rachas, etc.
        """
        bonus = 0

        try:
            # Bonus por racha diaria (1 punto por día de racha, máximo 15)
            racha_actual = EntrenamientoGamificacionService._calcular_racha_actual(cliente)
            bonus_racha = min(15, racha_actual)
            bonus += bonus_racha

            # Bonus por entrenar en fin de semana (+3 puntos)
            if entreno_realizado.fecha.weekday() >= 5:  # Sábado o domingo
                bonus += 3

            # Bonus por récords personales
            records_rotos = entreno_realizado.ejercicios_realizados.filter(
                nuevo_record=True
            ).count()
            bonus += records_rotos * 5  # 5 puntos por récord

            logger.debug(f"Puntos bonus: {bonus} (racha: {bonus_racha}, records: {records_rotos})")

        except Exception as e:
            logger.error(f"Error calculando puntos bonus: {e}")

        return bonus

    @staticmethod
    def _calcular_racha_actual(cliente):
        """
        Calcula la racha actual de días consecutivos entrenando
        """
        try:
            from entrenos.models import EntrenoRealizado

            entrenamientos = EntrenoRealizado.objects.filter(
                cliente=cliente
            ).order_by('-fecha')

            if not entrenamientos.exists():
                return 0

            # Obtener fechas únicas
            fechas = []
            for entreno in entrenamientos:
                if entreno.fecha not in fechas:
                    fechas.append(entreno.fecha)

            if not fechas:
                return 0

            # Calcular racha
            racha = 1
            fecha_anterior = fechas[0]

            for fecha in fechas[1:]:
                diferencia = (fecha_anterior - fecha).days
                if diferencia == 1:
                    racha += 1
                    fecha_anterior = fecha
                else:
                    break

            return racha

        except Exception as e:
            logger.error(f"Error calculando racha actual: {e}")
            return 0

    @staticmethod
    def obtener_resumen_gamificacion(cliente):
        """
        Obtiene un resumen del estado de gamificación del cliente
        Para usar en templates
        """
        try:
            from logros.models import PerfilGamificacion, PruebaUsuario, Arquetipo

            perfil = PerfilGamificacion.objects.filter(cliente=cliente).first()
            if not perfil:
                return {
                    'tiene_perfil': False,
                    'nivel_actual': 'El Aspirante Calvo',
                    'puntos_actuales': 0,
                    'puntos_siguiente': 500,
                    'porcentaje_progreso': 0,
                    'pruebas_activas': [],
                    'racha_actual': 0
                }

            # Calcular siguiente nivel
            siguiente_arquetipo = None
            if perfil.arquetipo_actual:
                siguiente_arquetipo = Arquetipo.objects.filter(
                    nivel=perfil.arquetipo_actual.nivel + 1
                ).first()
            else:
                siguiente_arquetipo = Arquetipo.objects.filter(nivel=1).first()

            # Calcular progreso
            puntos_actuales = perfil.puntos_totales
            puntos_siguiente = siguiente_arquetipo.puntos_requeridos if siguiente_arquetipo else 500
            puntos_nivel_actual = perfil.arquetipo_actual.puntos_requeridos if perfil.arquetipo_actual else 0

            progreso = puntos_actuales - puntos_nivel_actual
            total_necesario = puntos_siguiente - puntos_nivel_actual
            porcentaje = min(100, (progreso / total_necesario * 100)) if total_necesario > 0 else 0

            # Obtener pruebas activas
            pruebas_activas = []
            if perfil.arquetipo_actual:
                pruebas_activas = PruebaUsuario.objects.filter(
                    cliente=cliente,
                    prueba__arquetipo=perfil.arquetipo_actual,
                    completada=False
                ).select_related('prueba')[:3]

            return {
                'tiene_perfil': True,
                'perfil': perfil,
                'nivel_actual': perfil.arquetipo_actual.titulo_arquetipo if perfil.arquetipo_actual else 'El Aspirante Calvo',
                'puntos_actuales': puntos_actuales,
                'puntos_siguiente': puntos_siguiente,
                'porcentaje_progreso': int(porcentaje),
                'pruebas_activas': pruebas_activas,
                'siguiente_nivel': siguiente_arquetipo.titulo_arquetipo if siguiente_arquetipo else 'Máximo Nivel',
                'racha_actual': EntrenamientoGamificacionService._calcular_racha_actual(cliente)
            }

        except Exception as e:
            logger.error(f"Error obteniendo resumen de gamificación: {e}")
            return {
                'tiene_perfil': False,
                'error': str(e),
                'nivel_actual': 'Error',
                'puntos_actuales': 0,
                'puntos_siguiente': 0,
                'porcentaje_progreso': 0,
                'pruebas_activas': [],
                'racha_actual': 0
            }
