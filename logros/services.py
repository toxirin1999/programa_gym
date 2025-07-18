from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .logging_config import gamification_logger as logger
import logging
from django.db.models import Sum, Count, Max, Min, Avg
from .models import (
    PerfilGamificacion, Logro, Quest, LogroUsuario,
    QuestUsuario, HistorialPuntos, Nivel
)
from entrenos.models import EntrenoRealizado, SerieRealizada
from decimal import Decimal

logger = logging.getLogger(__name__)

# logros/services.py - Añadir nueva clase

import pandas as pd
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from django.db.models import Count, Sum, Avg, Max, Min, F, Q
from django.utils import timezone
from datetime import timedelta, datetime


class AnalisisGamificacionService:
    """
    Servicio para analizar datos de gamificación y generar insights.
    """

    @classmethod
    def generar_grafico_base64(cls, plt_figure):
        """Convierte un gráfico matplotlib a una imagen base64 para HTML"""
        buffer = io.BytesIO()
        plt_figure.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        imagen_png = buffer.getvalue()
        buffer.close()

        # Convertir a base64
        imagen_base64 = base64.b64encode(imagen_png).decode('utf-8')
        return f"data:image/png;base64,{imagen_base64}"

    @classmethod
    def analisis_progreso_cliente(cls, cliente, periodo_dias=90):
        """
        Analiza el progreso de un cliente en un período determinado.

        Args:
            cliente: Objeto Cliente
            periodo_dias: Número de días a analizar (por defecto 90)

        Returns:
            dict: Resultados del análisis
        """
        from entrenos.models import EntrenoRealizado, SerieRealizada
        from .models import PerfilGamificacion, LogroUsuario, QuestUsuario, HistorialPuntos

        fecha_inicio = timezone.now() - timedelta(days=periodo_dias)

        # Obtener datos de entrenamientos
        entrenos = EntrenoRealizado.objects.filter(
            cliente=cliente,
            fecha__gte=fecha_inicio
        ).order_by('fecha')

        # Obtener perfil de gamificación
        perfil = PerfilGamificacion.objects.filter(cliente=cliente).first()

        if not perfil or entrenos.count() == 0:
            return {
                'error': 'No hay suficientes datos para realizar el análisis',
                'cliente': cliente,
                'periodo_dias': periodo_dias
            }

        # Análisis de frecuencia de entrenamientos
        entrenos_por_semana = cls.calcular_frecuencia_entrenos(entrenos)

        # Análisis de volumen de entrenamiento
        volumen_por_semana = cls.calcular_volumen_entrenos(entrenos)

        # Análisis de progreso por ejercicio
        progreso_ejercicios = cls.analizar_progreso_ejercicios(cliente, fecha_inicio)

        # Análisis de logros y misiones
        analisis_logros = cls.analizar_logros_misiones(perfil, fecha_inicio)

        # Análisis de puntos y niveles
        analisis_puntos = cls.analizar_puntos(perfil, fecha_inicio)

        # Generar gráficos
        graficos = cls.generar_graficos_analisis(
            entrenos_por_semana,
            volumen_por_semana,
            progreso_ejercicios,
            analisis_logros,
            analisis_puntos
        )

        # Generar recomendaciones
        recomendaciones = cls.generar_recomendaciones(
            entrenos_por_semana,
            volumen_por_semana,
            progreso_ejercicios,
            analisis_logros
        )

        return {
            'cliente': cliente,
            'periodo_dias': periodo_dias,
            'entrenos_totales': entrenos.count(),
            'entrenos_por_semana': entrenos_por_semana,
            'volumen_por_semana': volumen_por_semana,
            'progreso_ejercicios': progreso_ejercicios,
            'analisis_logros': analisis_logros,
            'analisis_puntos': analisis_puntos,
            'graficos': graficos,
            'recomendaciones': recomendaciones
        }

    @classmethod
    def calcular_frecuencia_entrenos(cls, entrenos):
        """Calcula la frecuencia de entrenamientos por semana"""
        if not entrenos:
            return []

        # Convertir a DataFrame para facilitar el análisis
        entrenos_data = [{
            'id': e.id,
            'fecha': e.fecha,
            'semana': e.fecha.isocalendar()[1],  # Número de semana ISO
            'año': e.fecha.isocalendar()[0]  # Año
        } for e in entrenos]

        df = pd.DataFrame(entrenos_data)

        # Agrupar por semana y contar
        if not df.empty:
            df['semana_año'] = df['año'].astype(str) + '-' + df['semana'].astype(str)
            frecuencia = df.groupby('semana_año').size().reset_index(name='count')

            # Convertir a formato para el frontend
            resultado = [{
                'semana': row['semana_año'],
                'entrenamientos': row['count']
            } for _, row in frecuencia.iterrows()]

            return resultado

        return []

    @classmethod
    def calcular_volumen_entrenos(cls, entrenos):
        """Calcula el volumen de entrenamiento (peso total) por semana"""
        from entrenos.models import SerieRealizada

        if not entrenos:
            return []

        # Obtener todas las series de estos entrenamientos
        series_ids = [e.id for e in entrenos]
        series = SerieRealizada.objects.filter(
            entreno_id__in=series_ids,
            completado=True
        ).select_related('entreno')

        # Preparar datos para análisis
        series_data = [{
            'entreno_id': s.entreno_id,
            'fecha': s.entreno.fecha,
            'semana': s.entreno.fecha.isocalendar()[1],
            'año': s.entreno.fecha.isocalendar()[0],
            'volumen': float(s.peso_kg) * s.repeticiones if s.peso_kg else 0
        } for s in series]

        df = pd.DataFrame(series_data)

        # Agrupar por semana y sumar volumen
        if not df.empty:
            df['semana_año'] = df['año'].astype(str) + '-' + df['semana'].astype(str)
            volumen = df.groupby('semana_año')['volumen'].sum().reset_index()

            # Convertir a formato para el frontend
            resultado = [{
                'semana': row['semana_año'],
                'volumen': round(row['volumen'], 2)
            } for _, row in volumen.iterrows()]

            return resultado

        return []

    @classmethod
    def analizar_progreso_ejercicios(cls, cliente, fecha_inicio):
        """Analiza el progreso en los principales ejercicios"""
        from entrenos.models import SerieRealizada

        # Obtener los 5 ejercicios más frecuentes
        ejercicios_top = SerieRealizada.objects.filter(
            entreno__cliente=cliente,
            entreno__fecha__gte=fecha_inicio,
            completado=True
        ).values('ejercicio__nombre').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        resultados = []

        for ejercicio_data in ejercicios_top:
            nombre_ejercicio = ejercicio_data['ejercicio__nombre']

            # Obtener series de este ejercicio ordenadas por fecha
            series = SerieRealizada.objects.filter(
                entreno__cliente=cliente,
                entreno__fecha__gte=fecha_inicio,
                ejercicio__nombre=nombre_ejercicio,
                completado=True
            ).select_related('entreno').order_by('entreno__fecha')

            if not series:
                continue

            # Calcular peso máximo por entrenamiento
            entrenos_pesos = {}
            for serie in series:
                fecha = serie.entreno.fecha
                peso = float(serie.peso_kg) if serie.peso_kg else 0

                if fecha not in entrenos_pesos or peso > entrenos_pesos[fecha]:
                    entrenos_pesos[fecha] = peso

            # Convertir a lista ordenada
            progreso = [{'fecha': fecha, 'peso': peso} for fecha, peso in sorted(entrenos_pesos.items())]

            # Calcular tendencia
            if len(progreso) >= 2:
                primer_peso = progreso[0]['peso']
                ultimo_peso = progreso[-1]['peso']
                cambio_porcentual = ((ultimo_peso - primer_peso) / primer_peso * 100) if primer_peso > 0 else 0
            else:
                cambio_porcentual = 0

            resultados.append({
                'ejercicio': nombre_ejercicio,
                'progreso': progreso,
                'cambio_porcentual': round(cambio_porcentual, 2)
            })

        return resultados

    @classmethod
    def analizar_logros_misiones(cls, perfil, fecha_inicio):
        """Analiza los logros y misiones completados en el período"""
        from .models import LogroUsuario, QuestUsuario

        # Logros desbloqueados en el período
        logros = LogroUsuario.objects.filter(
            perfil=perfil,
            completado=True,
            fecha_desbloqueo__gte=fecha_inicio
        ).select_related('logro', 'logro__tipo')

        # Misiones completadas en el período
        misiones = QuestUsuario.objects.filter(
            perfil=perfil,
            completada=True,
            fecha_fin__gte=fecha_inicio
        ).select_related('quest', 'quest__tipo')

        # Agrupar logros por tipo
        logros_por_tipo = {}
        for logro in logros:
            tipo = logro.logro.tipo.get_categoria_display()
            if tipo not in logros_por_tipo:
                logros_por_tipo[tipo] = []

            logros_por_tipo[tipo].append({
                'nombre': logro.logro.nombre,
                'fecha': logro.fecha_desbloqueo,
                'puntos': logro.logro.puntos_recompensa
            })

        # Agrupar misiones por tipo
        misiones_por_tipo = {}
        for mision in misiones:
            tipo = mision.quest.tipo.get_periodo_display()
            if tipo not in misiones_por_tipo:
                misiones_por_tipo[tipo] = []

            misiones_por_tipo[tipo].append({
                'nombre': mision.quest.nombre,
                'fecha': mision.fecha_fin,
                'puntos': mision.quest.puntos_recompensa
            })

        return {
            'logros_totales': logros.count(),
            'misiones_totales': misiones.count(),
            'logros_por_tipo': logros_por_tipo,
            'misiones_por_tipo': misiones_por_tipo
        }

    @classmethod
    def analizar_puntos(cls, perfil, fecha_inicio):
        """Analiza la evolución de puntos en el período"""
        from .models import HistorialPuntos

        # Obtener historial de puntos
        historial = HistorialPuntos.objects.filter(
            perfil=perfil,
            fecha__gte=fecha_inicio
        ).order_by('fecha')

        # Preparar datos para análisis
        puntos_data = [{
            'fecha': h.fecha.date(),
            'puntos': h.puntos,
            'origen': 'Logro' if h.logro else ('Misión' if h.quest else 'Entrenamiento')
        } for h in historial]

        df = pd.DataFrame(puntos_data)

        # Calcular puntos acumulados
        if not df.empty:
            # Agrupar por fecha y origen
            puntos_por_dia = df.groupby(['fecha', 'origen'])['puntos'].sum().reset_index()

            # Calcular puntos acumulados
            puntos_acumulados = []
            total_acumulado = perfil.puntos_totales - df['puntos'].sum()  # Puntos antes del período

            for fecha in sorted(df['fecha'].unique()):
                puntos_dia = puntos_por_dia[puntos_por_dia['fecha'] == fecha]

                for _, row in puntos_dia.iterrows():
                    total_acumulado += row['puntos']
                    puntos_acumulados.append({
                        'fecha': row['fecha'].strftime('%Y-%m-%d'),
                        'origen': row['origen'],
                        'puntos': row['puntos'],
                        'acumulado': total_acumulado
                    })

            # Calcular promedios y tendencias
            promedio_diario = df.groupby('fecha')['puntos'].sum().mean() if len(df) > 0 else 0
            promedio_semanal = df.groupby([pd.Grouper(key='fecha', freq='W')])['puntos'].sum().mean() if len(
                df) > 0 else 0

            return {
                'puntos_periodo': df['puntos'].sum(),
                'promedio_diario': round(promedio_diario, 2),
                'promedio_semanal': round(promedio_semanal, 2),
                'puntos_acumulados': puntos_acumulados
            }

        return {
            'puntos_periodo': 0,
            'promedio_diario': 0,
            'promedio_semanal': 0,
            'puntos_acumulados': []
        }

    @classmethod
    def generar_graficos_analisis(cls, entrenos_por_semana, volumen_por_semana,
                                  progreso_ejercicios, analisis_logros, analisis_puntos):
        """Genera gráficos para visualizar los análisis"""
        graficos = {}

        # 1. Gráfico de frecuencia de entrenamientos
        if entrenos_por_semana:
            plt.figure(figsize=(10, 5))
            df = pd.DataFrame(entrenos_por_semana)
            plt.bar(df['semana'], df['entrenamientos'], color='#4287f5')
            plt.title('Frecuencia de Entrenamientos por Semana')
            plt.xlabel('Semana')
            plt.ylabel('Número de Entrenamientos')
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['frecuencia_entrenos'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 2. Gráfico de volumen de entrenamiento
        if volumen_por_semana:
            plt.figure(figsize=(10, 5))
            df = pd.DataFrame(volumen_por_semana)
            plt.plot(df['semana'], df['volumen'], marker='o', linestyle='-', color='#32FF00')
            plt.title('Volumen de Entrenamiento por Semana')
            plt.xlabel('Semana')
            plt.ylabel('Volumen Total (kg)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['volumen_entrenos'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 3. Gráfico de progreso por ejercicio
        if progreso_ejercicios:
            plt.figure(figsize=(12, 6))
            for i, ejercicio in enumerate(progreso_ejercicios):
                if ejercicio['progreso']:
                    fechas = [p['fecha'] for p in ejercicio['progreso']]
                    pesos = [p['peso'] for p in ejercicio['progreso']]
                    plt.plot(fechas, pesos, marker='o', label=ejercicio['ejercicio'])

            plt.title('Progreso de Peso por Ejercicio')
            plt.xlabel('Fecha')
            plt.ylabel('Peso Máximo (kg)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['progreso_ejercicios'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 4. Gráfico de logros y misiones
        if analisis_logros['logros_totales'] > 0 or analisis_logros['misiones_totales'] > 0:
            plt.figure(figsize=(10, 5))

            # Preparar datos
            categorias = []
            valores = []

            # Logros por tipo
            for tipo, logros in analisis_logros['logros_por_tipo'].items():
                categorias.append(f"Logros: {tipo}")
                valores.append(len(logros))

            # Misiones por tipo
            for tipo, misiones in analisis_logros['misiones_por_tipo'].items():
                categorias.append(f"Misiones: {tipo}")
                valores.append(len(misiones))

            # Crear gráfico
            plt.bar(categorias, valores, color=['#4287f5', '#32FF00', '#FFD700', '#FF69B4'])
            plt.title('Logros y Misiones Completados por Tipo')
            plt.xlabel('Tipo')
            plt.ylabel('Cantidad')
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['logros_misiones'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 5. Gráfico de evolución de puntos
        if analisis_puntos['puntos_acumulados']:
            plt.figure(figsize=(10, 5))

            # Preparar datos
            df = pd.DataFrame(analisis_puntos['puntos_acumulados'])

            # Crear gráfico
            plt.plot(df['fecha'], df['acumulado'], marker='o', linestyle='-', color='#FFD700')
            plt.title('Evolución de Puntos Acumulados')
            plt.xlabel('Fecha')
            plt.ylabel('Puntos Totales')
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['evolucion_puntos'] = cls.generar_grafico_base64(plt)
            plt.close()

        return graficos

    @classmethod
    def generar_recomendaciones(cls, entrenos_por_semana, volumen_por_semana,
                                progreso_ejercicios, analisis_logros):
        """Genera recomendaciones basadas en los análisis"""
        recomendaciones = []

        # 1. Recomendaciones de frecuencia de entrenamientos
        if entrenos_por_semana:
            df = pd.DataFrame(entrenos_por_semana)
            promedio_entrenos = df['entrenamientos'].mean() if len(df) > 0 else 0

            if promedio_entrenos < 2:
                recomendaciones.append({
                    'tipo': 'frecuencia',
                    'mensaje': 'Considera aumentar la frecuencia de entrenamientos a al menos 3 por semana para mejorar resultados.',
                    'icono': '📅'
                })
            elif promedio_entrenos > 5:
                recomendaciones.append({
                    'tipo': 'frecuencia',
                    'mensaje': 'Estás entrenando con mucha frecuencia. Asegúrate de incluir suficientes días de descanso para recuperación.',
                    'icono': '🛌'
                })

        # 2. Recomendaciones de volumen
        if volumen_por_semana and len(volumen_por_semana) >= 2:
            df = pd.DataFrame(volumen_por_semana)

            # Verificar tendencia
            if len(df) >= 3:
                primeras_semanas = df['volumen'].iloc[:len(df) // 2].mean()
                ultimas_semanas = df['volumen'].iloc[len(df) // 2:].mean()

                if ultimas_semanas < primeras_semanas * 0.8:
                    recomendaciones.append({
                        'tipo': 'volumen',
                        'mensaje': 'Tu volumen de entrenamiento ha disminuido. Considera aumentar gradualmente la intensidad o duración.',
                        'icono': '📉'
                    })
                elif ultimas_semanas > primeras_semanas * 1.5:
                    recomendaciones.append({
                        'tipo': 'volumen',
                        'mensaje': 'Has aumentado significativamente tu volumen. Asegúrate de no sobreentrenar y mantener buena técnica.',
                        'icono': '📈'
                    })

        # 3. Recomendaciones de progreso por ejercicio
        if progreso_ejercicios:
            ejercicios_estancados = []

            for ejercicio in progreso_ejercicios:
                if abs(ejercicio['cambio_porcentual']) < 2 and len(ejercicio['progreso']) >= 4:
                    ejercicios_estancados.append(ejercicio['ejercicio'])

            if ejercicios_estancados:
                recomendaciones.append({
                    'tipo': 'progreso',
                    'mensaje': f'Parece que estás estancado en: {", ".join(ejercicios_estancados)}. Considera cambiar variables como series, repeticiones o técnica.',
                    'icono': '🔄'
                })

        # 4. Recomendaciones de logros y misiones
        if analisis_logros:
            if analisis_logros['logros_totales'] == 0:
                recomendaciones.append({
                    'tipo': 'logros',
                    'mensaje': 'No has desbloqueado logros recientemente. Revisa la lista de logros disponibles para nuevos objetivos.',
                    'icono': '🏆'
                })

            if analisis_logros['misiones_totales'] == 0:
                recomendaciones.append({
                    'tipo': 'misiones',
                    'mensaje': 'No has completado misiones recientemente. Las misiones pueden ayudarte a mantener la motivación.',
                    'icono': '🎯'
                })

        # 5. Recomendaciones generales
        if len(recomendaciones) == 0:
            recomendaciones.append({
                'tipo': 'general',
                'mensaje': '¡Excelente trabajo! Mantén tu consistencia actual para seguir progresando.',
                'icono': '👍'
            })

        return recomendaciones

    @classmethod
    def analisis_global_clientes(cls, periodo_dias=90):
        """
        Realiza un análisis global de todos los clientes.

        Args:
            periodo_dias: Número de días a analizar (por defecto 90)

        Returns:
            dict: Resultados del análisis global
        """
        from clientes.models import Cliente
        from entrenos.models import EntrenoRealizado
        from .models import PerfilGamificacion, LogroUsuario, QuestUsuario

        fecha_inicio = timezone.now() - timedelta(days=periodo_dias)

        # Obtener todos los clientes activos
        clientes = Cliente.objects.filter(
            entrenorealizado__fecha__gte=fecha_inicio
        ).distinct()

        if not clientes:
            return {
                'error': 'No hay clientes activos en el período seleccionado',
                'periodo_dias': periodo_dias
            }

        # Estadísticas generales
        total_entrenos = EntrenoRealizado.objects.filter(
            fecha__gte=fecha_inicio
        ).count()

        total_logros = LogroUsuario.objects.filter(
            completado=True,
            fecha_desbloqueo__gte=fecha_inicio
        ).count()

        total_misiones = QuestUsuario.objects.filter(
            completada=True,
            fecha_fin__gte=fecha_inicio
        ).count()

        # Análisis por cliente
        clientes_data = []
        for cliente in clientes:
            perfil = PerfilGamificacion.objects.filter(cliente=cliente).first()
            if not perfil:
                continue

            entrenos_cliente = EntrenoRealizado.objects.filter(
                cliente=cliente,
                fecha__gte=fecha_inicio
            ).count()

            logros_cliente = LogroUsuario.objects.filter(
                perfil=perfil,
                completado=True,
                fecha_desbloqueo__gte=fecha_inicio
            ).count()

            misiones_cliente = QuestUsuario.objects.filter(
                perfil=perfil,
                completada=True,
                fecha_fin__gte=fecha_inicio
            ).count()

            clientes_data.append({
                'cliente': cliente,
                'entrenos': entrenos_cliente,
                'logros': logros_cliente,
                'misiones': misiones_cliente,
                'puntos': perfil.puntos_totales,
                'nivel': perfil.nivel_actual.numero if perfil.nivel_actual else 1
            })

        # Ordenar por puntos (ranking)
        clientes_data.sort(key=lambda x: x['puntos'], reverse=True)

        # Generar gráficos
        graficos = cls.generar_graficos_globales(clientes_data, fecha_inicio)

        return {
            'periodo_dias': periodo_dias,
            'total_clientes': len(clientes),
            'total_entrenos': total_entrenos,
            'total_logros': total_logros,
            'total_misiones': total_misiones,
            'promedio_entrenos_por_cliente': total_entrenos / len(clientes) if len(clientes) > 0 else 0,
            'promedio_logros_por_cliente': total_logros / len(clientes) if len(clientes) > 0 else 0,
            'promedio_misiones_por_cliente': total_misiones / len(clientes) if len(clientes) > 0 else 0,
            'clientes_data': clientes_data,
            'graficos': graficos
        }

    @classmethod
    def generar_graficos_globales(cls, clientes_data, fecha_inicio):
        """Genera gráficos para el análisis global"""
        graficos = {}

        # 1. Gráfico de ranking de clientes por puntos
        if clientes_data:
            plt.figure(figsize=(12, 6))

            # Limitar a los 10 mejores para claridad
            top_clientes = clientes_data[:10]

            nombres = [c['cliente'].nombre for c in top_clientes]
            puntos = [c['puntos'] for c in top_clientes]

            plt.bar(nombres, puntos, color='#4287f5')
            plt.title('Top 10 Clientes por Puntos')
            plt.xlabel('Cliente')
            plt.ylabel('Puntos Totales')
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['ranking_puntos'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 2. Gráfico de distribución de niveles
        if clientes_data:
            plt.figure(figsize=(10, 5))

            niveles = [c['nivel'] for c in clientes_data]
            nivel_counts = pd.Series(niveles).value_counts().sort_index()

            plt.bar(nivel_counts.index, nivel_counts.values, color='#32FF00')
            plt.title('Distribución de Niveles de Clientes')
            plt.xlabel('Nivel')
            plt.ylabel('Número de Clientes')
            plt.xticks(nivel_counts.index)
            plt.tight_layout()
            graficos['distribucion_niveles'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 3. Gráfico de actividad (entrenamientos, logros, misiones)
        if clientes_data:
            plt.figure(figsize=(12, 6))

            # Preparar datos
            df = pd.DataFrame(clientes_data)

            # Seleccionar los 10 clientes más activos por número total de actividades
            df['total_actividades'] = df['entrenos'] + df['logros'] + df['misiones']
            top_activos = df.nlargest(10, 'total_actividades')

            # Crear gráfico de barras apiladas
            nombres = [c['cliente'].nombre for _, c in top_activos.iterrows()]

            plt.bar(nombres, top_activos['entrenos'], label='Entrenamientos', color='#4287f5')
            plt.bar(nombres, top_activos['logros'], bottom=top_activos['entrenos'],
                    label='Logros', color='#32FF00')
            plt.bar(nombres, top_activos['misiones'],
                    bottom=top_activos['entrenos'] + top_activos['logros'],
                    label='Misiones', color='#FFD700')

            plt.title('Top 10 Clientes Más Activos')
            plt.xlabel('Cliente')
            plt.ylabel('Número de Actividades')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            graficos['clientes_activos'] = cls.generar_grafico_base64(plt)
            plt.close()

        # 4. Análisis de tendencia de entrenamientos global
        from entrenos.models import EntrenoRealizado

        # Obtener todos los entrenamientos en el período
        entrenos = EntrenoRealizado.objects.filter(
            fecha__gte=fecha_inicio
        ).order_by('fecha')

        if entrenos:
            # Convertir a DataFrame
            entrenos_data = [{
                'fecha': e.fecha,
                'semana': e.fecha.isocalendar()[1],
                'año': e.fecha.isocalendar()[0]
            } for e in entrenos]

            df = pd.DataFrame(entrenos_data)

            if not df.empty:
                df['semana_año'] = df['año'].astype(str) + '-' + df['semana'].astype(str)
                tendencia = df.groupby('semana_año').size().reset_index(name='count')

                plt.figure(figsize=(12, 5))
                plt.plot(tendencia['semana_año'], tendencia['count'], marker='o',
                         linestyle='-', color='#4287f5')
                plt.title('Tendencia de Entrenamientos por Semana')
                plt.xlabel('Semana')
                plt.ylabel('Número de Entrenamientos')
                plt.xticks(rotation=45)
                plt.tight_layout()
                graficos['tendencia_global'] = cls.generar_grafico_base64(plt)
                plt.close()

        return graficos


# logros/services.py

# (Mantén todas tus importaciones existentes y la clase AnalisisGamificacionService)
# ...

# ============================================================================
# VERSIÓN REFACTORIZADA DE GAMIFICACIONSERVICE
# ============================================================================

class GamificacionService:
    """
    Servicio unificado y transaccional para manejar la lógica de gamificación.
    Esta versión corregida asegura la consistencia de los datos.
    """

    @classmethod
    def procesar_entreno(cls, entreno):
        logger.info(f"Iniciando procesamiento de entreno para cliente {cliente_id}")

        try:
            # Usamos una transacción para garantizar que todas las actualizaciones
            # se realicen correctamente o ninguna lo haga.
            with transaction.atomic():
                # 1. Obtener el perfil, bloqueándolo para evitar condiciones de carrera.
                perfil, _ = PerfilGamificacion.objects.select_for_update().get_or_create(
                    cliente=entreno.cliente,
                    defaults={'nivel_actual': Nivel.objects.order_by('numero').first()}
                )

                # 2. Actualizar estadísticas básicas del perfil (rachas, contadores).
                cls._actualizar_estadisticas_base(perfil, entreno)

                # 3. Verificar TODOS los logros y misiones aplicables.
                # Este método interno se encargará de sumar puntos si se desbloquea algo.
                logros_desbloqueados = cls._verificar_todos_los_logros(perfil)

                # 4. Actualizar el nivel del usuario al final, después de sumar todos los puntos.
                subio_nivel = perfil.actualizar_nivel()

                # 5. Guardar el perfil una sola vez al final de la transacción.
                perfil.save()

                # 6. (Opcional) Crear notificaciones para los eventos ocurridos.
                if subio_nivel:
                    # Lógica para notificar subida de nivel
                    logger.info(f"¡{perfil.cliente.nombre} ha subido al nivel {perfil.nivel_actual.numero}!")
                resultado = self._procesar_logros_usuario(cliente_id)

                logger.info(f"Procesamiento exitoso para cliente {cliente_id}: {resultado}")

                logger.info(
                    f"Entreno procesado para {perfil.cliente.nombre}. "
                    f"Puntos totales ahora: {perfil.puntos_totales}. "
                    f"Logros nuevos: {len(logros_desbloqueados)}."
                )

                return {
                    'puntos_totales': perfil.puntos_totales,
                    'logros_desbloqueados': logros_desbloqueados,
                    'subio_nivel': subio_nivel,
                    'nivel_actual': perfil.nivel_actual
                }

        except Exception as e:
            logger.error(
                f"Error crítico en GamificacionService.procesar_entreno para el cliente {entreno.cliente.id}: {e}",
                exc_info=True)
            return None

    @classmethod
    def _actualizar_estadisticas_base(cls, perfil, entreno):
        """
        Actualiza contadores y rachas. NO guarda el perfil, solo modifica el objeto.
        """
        perfil.entrenos_totales += 1

        # Lógica de racha mejorada
        if perfil.fecha_ultimo_entreno:
            # Asegurarse de que estamos comparando solo la parte de la fecha
            fecha_ultimo = perfil.fecha_ultimo_entreno.date() if isinstance(perfil.fecha_ultimo_entreno,
                                                                            timezone.datetime) else perfil.fecha_ultimo_entreno
            dias_diff = (entreno.fecha - fecha_ultimo).days

            if dias_diff == 1:
                perfil.racha_actual += 1
            elif dias_diff > 1:
                perfil.racha_actual = 1
            # Si dias_diff <= 0, es un entreno del mismo día o anterior, no afecta la racha.
        else:
            perfil.racha_actual = 1

        perfil.racha_maxima = max(perfil.racha_actual, perfil.racha_maxima)
        perfil.fecha_ultimo_entreno = entreno.fecha

    @classmethod
    def _verificar_todos_los_logros(cls, perfil):
        """
        Verifica todos los logros del juego. Si uno se desbloquea, suma los puntos
        al perfil y lo registra en el historial.
        """
        logros_desbloqueados_ahora = []

        # Obtenemos solo los logros que el usuario AÚN NO HA COMPLETADO para ser más eficientes.
        logros_pendientes = Logro.objects.exclude(usuarios__perfil=perfil, usuarios__completado=True)

        for logro in logros_pendientes:
            progreso_actual = cls._calcular_progreso_para_logro(perfil, logro)

            if progreso_actual >= logro.meta_valor:
                # ¡Logro desbloqueado!
                logro_usuario, _ = LogroUsuario.objects.get_or_create(perfil=perfil, logro=logro)

                if not logro_usuario.completado:
                    logro_usuario.completado = True
                    logro_usuario.progreso_actual = progreso_actual
                    logro_usuario.fecha_desbloqueo = timezone.now()
                    logro_usuario.save()

                    # Sumamos los puntos al perfil (el objeto, aún no se guarda en BD)
                    perfil.puntos_totales += logro.puntos_recompensa
                    logros_desbloqueados_ahora.append(logro)

                    # Creamos el registro histórico
                    HistorialPuntos.objects.create(
                        perfil=perfil,
                        puntos=logro.puntos_recompensa,
                        logro=logro,
                        descripcion=f"Recompensa por logro: {logro.nombre}"
                    )

        return logros_desbloqueados_ahora

    @classmethod
    def _calcular_progreso_para_logro(cls, perfil, logro):
        """
        Calcula el progreso actual para un logro específico.
        Esta función es el "cerebro" que conecta las acciones con los logros.
        """
        identificador = logro.nombre.lower()
        cliente_id = perfil.cliente_id

        try:
            # --- LOGROS BASADOS EN NÚMERO DE ENTRENAMIENTOS ---
            if "liftin principiante" in identificador:
                return EntrenoRealizado.objects.filter(cliente_id=cliente_id, fuente_datos='liftin').count()

            # --- LOGROS BASADOS EN MÉTRICAS ACUMULADAS ---
            if "quemador principiante" in identificador:
                # NOTA: Este logro debería ser sobre CALORÍAS TOTALES, no de un solo entreno.
                # Si es por un solo entreno, la lógica debe estar en otro lado.
                # Asumimos que es por el total acumulado.
                resultado = EntrenoRealizado.objects.filter(cliente_id=cliente_id).aggregate(
                    total=Sum('calorias_quemadas'))
                return resultado['total'] or 0

            # --- LOGROS DE RACHA ---
            if "racha" in identificador:
                return perfil.racha_actual

            # ... Añade aquí el resto de tus condiciones de logros ...

        except Exception as e:
            logger.error(f"Error calculando progreso para logro '{logro.nombre}' y perfil {perfil.id}: {e}")
            return 0

        return 0

    @classmethod
    def actualizar_estadisticas_perfil(cls, perfil, entreno):
        """
        Calcula puntos por la actividad del entreno y actualiza contadores y racha.
        Devuelve los puntos ganados solo por la actividad.
        """
        # Fórmula de puntos por actividad (puedes ajustarla)
        puntos_actividad = 100  # Puntos base por entrenar
        if entreno.volumen_total_kg:
            puntos_actividad += int(entreno.volumen_total_kg / 20)
        if entreno.calorias_quemadas:
            puntos_actividad += int(entreno.calorias_quemadas / 5)

        perfil.puntos_totales += puntos_actividad
        perfil.entrenos_totales += 1

        # Lógica de racha
        if perfil.fecha_ultimo_entreno:
            dias_diff = (entreno.fecha - perfil.fecha_ultimo_entreno.date()).days
            if dias_diff == 1:
                perfil.racha_actual += 1
            elif dias_diff > 1:
                perfil.racha_actual = 1
        else:
            perfil.racha_actual = 1

        perfil.racha_maxima = max(perfil.racha_actual, perfil.racha_maxima)
        perfil.fecha_ultimo_entreno = entreno.fecha

        perfil.save()
        return puntos_actividad

    @classmethod
    def verificar_y_otorgar_logros(cls, perfil):
        """
        Verifica todos los logros para un perfil y los otorga si se cumplen las condiciones.
        """
        logros_desbloqueados_en_esta_llamada = []
        todos_los_logros_del_juego = Logro.objects.all()

        for logro in todos_los_logros_del_juego:
            logro_usuario, created = LogroUsuario.objects.get_or_create(
                perfil=perfil,
                logro=logro,
                defaults={'progreso_actual': 0, 'completado': False}
            )

            if logro_usuario.completado:
                continue

            progreso_actual = cls.calcular_progreso_logro(perfil, logro)
            logro_usuario.progreso_actual = progreso_actual

            if progreso_actual >= logro.meta_valor:
                logro_usuario.completado = True
                logro_usuario.fecha_desbloqueo = timezone.now()

                puntos_recompensa = logro.puntos_recompensa
                perfil.puntos_totales += puntos_recompensa

                logro_usuario.save()
                perfil.save()

                HistorialPuntos.objects.create(
                    perfil=perfil,
                    puntos=puntos_recompensa,
                    logro=logro,
                    descripcion=f"Recompensa por logro: {logro.nombre}"
                )

                logros_desbloqueados_en_esta_llamada.append(logro)
                logger.info(
                    f"¡LOGRO DESBLOQUEADO para {perfil.cliente.nombre}: {logro.nombre} (+{puntos_recompensa} pts)!")
            else:
                logro_usuario.save()

        return logros_desbloqueados_en_esta_llamada

    @classmethod
    def calcular_progreso_logro(cls, perfil, logro):
        """
        Calcula el progreso actual de un cliente para un logro específico.
        VERSIÓN REFORZADA Y A PRUEBA DE ERRORES.
        """
        identificador = logro.nombre.lower()
        cliente_id = perfil.cliente.id  # Usamos el ID del cliente para las consultas

        try:
            # --- LOGROS BASADOS EN NÚMERO DE ENTRENAMIENTOS ---
            if "liftin principiante" in identificador:
                # Consulta explícita y segura
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fuente_datos='liftin'
                ).count()

            if "entrenamientos totales" in identificador:
                # Este dato ya está en el perfil, es más eficiente usarlo
                return perfil.entrenos_totales

            # --- LOGROS BASADOS EN RACHA ---
            if "racha" in identificador:
                # Este dato también está en el perfil
                return perfil.racha_actual

            # --- LOGROS BASADOS EN MÉTRICAS ACUMULADAS ---
            if "quemador principiante" in identificador:
                # Consulta explícita con aggregate
                resultado = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).aggregate(
                    total_calorias=Sum('calorias_quemadas')
                )
                # Devolver el total o 0 si es None
                return resultado['total_calorias'] or 0

            if "volumen total" in identificador:
                resultado = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).aggregate(
                    total_volumen=Sum('volumen_total_kg')
                )
                return int(resultado['total_volumen'] or 0)

            # ... Puedes añadir más condiciones para otros logros aquí ...

        except Exception as e:
            logger.error(f"Error calculando progreso para logro '{logro.nombre}' y perfil {perfil.id}: {e}")
            return 0  # Si hay cualquier error en la consulta, devuelve 0 para no bloquear el sistema

        return 0  # Devuelve 0 si el logro no se reconoce

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
                if serie.ejercicio.grupo_muscular in ['Piernas', 'Espalda']:
                    coeficiente = Decimal("1.5")
                elif serie.ejercicio.grupo_muscular in ['Pecho', 'Hombros']:
                    coeficiente = Decimal("1.2")
                else:
                    coeficiente = Decimal("1.0")

                puntos_serie *= coeficiente

            puntos_totales += round(puntos_serie)

        # Bonificación por entrenamiento completo
        if series.count() > 0 and series.filter(completado=True).count() == series.count():
            puntos_totales += 50  # Bonus por completar todas las series

        return puntos_totales

    @classmethod
    def actualizar_estadisticas_perfil(cls, perfil, entreno):
        """
        Calcula puntos, actualiza racha y contadores. Devuelve los puntos ganados.
        """
        # Lógica de cálculo de puntos (puedes usar tu propia función aquí)
        puntos_entreno = 100 + (entreno.volumen_total_kg / 10) if entreno.volumen_total_kg else 100
        puntos_entreno = int(puntos_entreno)

        perfil.puntos_totales += puntos_entreno
        perfil.entrenos_totales += 1

        # Lógica de racha
        if perfil.fecha_ultimo_entreno:
            dias_diff = (entreno.fecha - perfil.fecha_ultimo_entreno.date()).days
            if dias_diff == 1:
                perfil.racha_actual += 1
            elif dias_diff > 1:
                perfil.racha_actual = 1
        else:
            perfil.racha_actual = 1

        perfil.racha_maxima = max(perfil.racha_actual, perfil.racha_maxima)
        perfil.fecha_ultimo_entreno = entreno.fecha
        perfil.save()

        return puntos_entreno

        @classmethod
        def calcular_progreso_logro(cls, perfil, logro):
            """
            Calcula el progreso actual de un cliente para un logro específico.
            Esta es la función más importante para personalizar.
            """
            # Identificador del logro (usamos el nombre en minúsculas para flexibilidad)
            identificador = logro.nombre.lower()

            # --- LOGROS BASADOS EN ENTRENAMIENTOS ---
            if "liftin principiante" in identificador or "entrenamientos de liftin" in logro.descripcion.lower():
                return EntrenoRealizado.objects.filter(cliente=perfil.cliente, fuente_datos='liftin').count()

            if "entrenamientos totales" in identificador:
                return perfil.entrenos_totales

            # --- LOGROS BASADOS EN RACHA ---
            if "racha" in identificador:
                return perfil.racha_actual

            # --- LOGROS BASADOS EN CALORÍAS ---
            if "calorías quemadas" in logro.descripcion.lower():
                total_calorias = EntrenoRealizado.objects.filter(cliente=perfil.cliente).aggregate(
                    total=Sum('calorias_quemadas')
                )['total'] or 0
                return total_calorias

            # --- LOGROS BASADOS EN VOLUMEN ---
            if "volumen total" in logro.descripcion.lower():
                total_volumen = EntrenoRealizado.objects.filter(cliente=perfil.cliente).aggregate(
                    total=Sum('volumen_total_kg')
                )['total'] or 0
                return int(total_volumen)

            # Añade aquí más condiciones para otros logros...
            # if "otro logro" in identificador:
            #     return ...

            return 0  # Devuelve 0 si no se reconoce el logro

    # Solución Recomendada para services.py
    @classmethod
    def verificar_logros(perfil, entreno):
        """
        Verifica y otorga logros basados en el entrenamiento del cliente.
        """
        try:
            # Intenta obtener una misión existente
            quest_usuario = perfil.quests.first()

            # Si no existe, crear una misión inicial de prueba (opcional)
            if quest_usuario is None:
                from .models import QuestUsuario, Quest
                primera_quest = Quest.objects.first()  # Usa una misión base

                if primera_quest:
                    quest_usuario = QuestUsuario.objects.create(
                        perfil=perfil,
                        quest=primera_quest,
                        progreso_actual=0,
                        completada=False
                    )

            # Verificación de ejemplo (logro por nivel de misión)
            if quest_usuario and hasattr(quest_usuario, 'nivel') and quest_usuario.nivel >= 5:
                otorgar_logro_nivel_avanzado(perfil.cliente, entreno, quest_usuario)

            # Otras verificaciones
            verificar_otros_logros(perfil.cliente, entreno, quest_usuario)

        except AttributeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error de atributo al verificar logros para perfil {perfil.id}: {e}")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error inesperado en verificar logros para perfil {perfil.id}: {e}")

    @classmethod
    def _verificar_logro_consistencia(cls, logro_usuario, perfil, entreno=None, tipo_logro=None):
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
    def _verificar_logro_superacion(cls, logro_usuario, perfil, entreno, tipo_logro=None):
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
    def _verificar_logro_especial(cls, logro_usuario, perfil, entreno, tipo_logro=None):
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
        if entreno and entreno.fecha == timezone.now().date():
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
    def _verificar_logro_exploracion(cls, logro_usuario, perfil, entreno, tipo_logro=None):
        """Verifica logros de tipo 'exploracion'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        actualizado = False

        # Verificar por nombre o patrón del logro
        if "aventurero del fitness" in nombre_logro:
            # Contar ejercicios diferentes realizados
            from django.db.models import Count
            from entrenos.models import SerieRealizada

            ejercicios_diferentes = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente
            ).values('ejercicio').distinct().count()

            logro_usuario.progreso_actual = ejercicios_diferentes
            logro_usuario.save()
            actualizado = True

        elif "maestro versátil" in nombre_logro:
            # Verificar entrenamientos para diferentes grupos musculares
            from django.db.models import Count
            from entrenos.models import SerieRealizada

            grupos_musculares = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente
            ).values('ejercicio__grupo_muscular').distinct().count()

            logro_usuario.progreso_actual = grupos_musculares
            logro_usuario.save()
            actualizado = True

        elif "explorador de rutinas" in nombre_logro:
            # Contar rutinas diferentes realizadas
            from django.db.models import Count
            from entrenos.models import EntrenoRealizado

            rutinas_diferentes = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente
            ).values('rutina').distinct().count()

            logro_usuario.progreso_actual = rutinas_diferentes
            logro_usuario.save()
            actualizado = True

        elif "maestro de técnicas" in nombre_logro:
            # Contar tipos diferentes de equipamiento usado
            from django.db.models import Count
            from entrenos.models import SerieRealizada

            equipamientos = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente
            ).values('ejercicio__equipamiento').distinct().count()

            logro_usuario.progreso_actual = equipamientos
            logro_usuario.save()
            actualizado = True

        return actualizado

    @classmethod
    def _verificar_logro_equilibrio(cls, logro_usuario, perfil, entreno, tipo_logro=None):
        """Verifica logros de tipo 'equilibrio'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        actualizado = False

        # Verificar por nombre o patrón del logro
        if "entrenamiento holístico" in nombre_logro:
            # Verificar si ha entrenado todos los grupos musculares en una semana
            from django.db.models import Count
            from entrenos.models import SerieRealizada
            from django.utils import timezone

            fecha_inicio = timezone.now() - timezone.timedelta(days=7)
            grupos_musculares_semana = SerieRealizada.objects.filter(
                entreno__cliente=perfil.cliente,
                entreno__fecha__gte=fecha_inicio
            ).values('ejercicio__grupo_muscular').distinct().count()

            # Asumimos que hay 5 grupos musculares principales
            total_grupos = 5

            if grupos_musculares_semana >= total_grupos:
                logro_usuario.progreso_actual = 1
            else:
                logro_usuario.progreso_actual = 0

            logro_usuario.save()
            actualizado = True

        elif "cuerpo simétrico" in nombre_logro:
            # Verificar equilibrio entre ejercicios de empuje y tracción
            from django.db.models import Count, Q
            from entrenos.models import EntrenoRealizado, SerieRealizada

            # Contar entrenamientos con equilibrio
            entrenamientos_equilibrados = 0

            # Obtener los últimos 10 entrenamientos
            ultimos_entrenos = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente
            ).order_by('-fecha')[:10]

            for entreno_obj in ultimos_entrenos:
                # Contar series de empuje y tracción
                series_empuje = SerieRealizada.objects.filter(
                    entreno=entreno_obj,
                    ejercicio__tipo='empuje'
                ).count()

                series_traccion = SerieRealizada.objects.filter(
                    entreno=entreno_obj,
                    ejercicio__tipo='traccion'
                ).count()

                # Verificar si hay equilibrio (diferencia menor al 20%)
                if series_empuje > 0 and series_traccion > 0:
                    ratio = min(series_empuje, series_traccion) / max(series_empuje, series_traccion)
                    if ratio >= 0.8:  # Al menos 80% de equilibrio
                        entrenamientos_equilibrados += 1

            logro_usuario.progreso_actual = entrenamientos_equilibrados
            logro_usuario.save()
            actualizado = True

        # Implementar verificaciones para otros logros de equilibrio...

        return actualizado

    @classmethod
    def _verificar_logro_social(cls, logro_usuario, perfil, entreno, tipo_logro=None):
        """Verifica logros de tipo 'social'"""
        # Este tipo de logro puede requerir datos adicionales que no están disponibles automáticamente
        # Por ejemplo, entrenamientos con compañeros, motivar a amigos, etc.
        # Podrías implementar una lógica básica y luego permitir actualizaciones manuales

        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        actualizado = False

        # Por ahora, simplemente mantenemos el progreso actual
        # Estos logros podrían actualizarse manualmente o mediante eventos específicos

        return actualizado

    @classmethod
    def _verificar_logro_tecnica(cls, logro_usuario, perfil, entreno, tipo_logro=None):
        """Verifica logros de tipo 'tecnica'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        actualizado = False

        # Estos logros podrían requerir evaluación manual o datos específicos
        # Por ejemplo, técnica perfecta validada por un entrenador

        if entreno and "forma perfecta" in nombre_logro:
            # Si el entrenamiento tiene una calificación de técnica alta
            if hasattr(entreno, 'calificacion_tecnica') and entreno.calificacion_tecnica >= 9:
                logro_usuario.progreso_actual += 1
                logro_usuario.save()
                actualizado = True

        # Implementar verificaciones para otros logros de técnica...

        return actualizado

    @classmethod
    def _verificar_logro_recuperacion(cls, logro_usuario, perfil, entreno, tipo_logro=None):
        """Verifica logros de tipo 'recuperacion'"""
        logro = logro_usuario.logro
        nombre_logro = logro.nombre.lower()
        actualizado = False

        # Estos logros podrían requerir datos adicionales como registros de sueño, hidratación, etc.

        if "maestro del descanso" in nombre_logro:
            # Este logro requeriría datos de sueño que probablemente no estén disponibles
            # Por ahora, simplemente mantenemos el progreso actual
            pass

        elif "hidratación perfecta" in nombre_logro:
            # Este logro requeriría datos de hidratación
            pass

        elif "maestro de la flexibilidad" in nombre_logro:
            # Si el entrenamiento incluye estiramientos
            if entreno and hasattr(entreno, 'incluye_estiramientos') and entreno.incluye_estiramientos:
                logro_usuario.progreso_actual += 1
                logro_usuario.save()
                actualizado = True

        # Implementar verificaciones para otros logros de recuperación...

        return actualizado

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

    @staticmethod
    def otorgar_logro_nivel_avanzado(usuario, entreno, quest_usuario):
        """
        Otorga logro cuando el usuario alcanza nivel 5 o superior
        """
        # Lógica real aquí
        pass

    @staticmethod
    def verificar_otros_logros(usuario, entreno, quest_usuario):
        """
        Verifica otros logros adicionales
        """
        # Lógica real aquí
        pass


# logros/services.py - Añadir nueva clase

class NotificacionService:
    """
    Servicio para gestionar las notificaciones de gamificación.
    """

    @classmethod
    def crear_notificacion_logro(cls, logro_usuario):
        """Crea una notificación cuando se desbloquea un logro"""
        from .models import Notificacion

        logro = logro_usuario.logro
        cliente = logro_usuario.perfil.cliente

        Notificacion.objects.create(
            cliente=cliente,
            tipo='logro',
            titulo=f"¡Logro Desbloqueado: {logro.nombre}!",
            mensaje=f"Has desbloqueado el logro '{logro.nombre}'. {logro.descripcion}",
            icono=logro.icono if logro.icono else '🏆',
            url_accion=f"/logros/perfil-gamificacion/{cliente.id}/"
        )

    @classmethod
    def crear_notificacion_mision(cls, quest_usuario):
        """Crea una notificación cuando se completa una misión"""
        from .models import Notificacion

        quest = quest_usuario.quest
        cliente = quest_usuario.perfil.cliente

        Notificacion.objects.create(
            cliente=cliente,
            tipo='mision',
            titulo=f"¡Misión Completada: {quest.nombre}!",
            mensaje=f"Has completado la misión '{quest.nombre}'. {quest.descripcion}",
            icono=quest.icono if quest.icono else '🎯',
            url_accion=f"/logros/perfil-gamificacion/{cliente.id}/"
        )

    @classmethod
    def crear_notificacion_nivel(cls, perfil, nivel_anterior, nivel_nuevo):
        """Crea una notificación cuando se sube de nivel"""
        from .models import Notificacion

        cliente = perfil.cliente

        Notificacion.objects.create(
            cliente=cliente,
            tipo='nivel',
            titulo=f"¡Has subido al nivel {nivel_nuevo.numero}!",
            mensaje=f"Felicidades, has alcanzado el nivel {nivel_nuevo.numero}: {nivel_nuevo.nombre}. Sigue así para desbloquear más recompensas.",
            icono='⬆️',
            url_accion=f"/logros/perfil-gamificacion/{cliente.id}/"
        )

    @classmethod
    def crear_notificacion_racha(cls, perfil, dias):
        """Crea una notificación cuando se alcanza una racha significativa"""
        from .models import Notificacion

        cliente = perfil.cliente

        # Solo notificar rachas significativas (7, 14, 30, 60, 90, etc.)
        if dias in [7, 14, 30, 60, 90, 180, 365]:
            Notificacion.objects.create(
                cliente=cliente,
                tipo='racha',
                titulo=f"¡Racha de {dias} días!",
                mensaje=f"Has mantenido una racha de entrenamiento durante {dias} días consecutivos. ¡Impresionante constancia!",
                icono='🔥',
                url_accion=f"/logros/perfil-gamificacion/{cliente.id}/"
            )

    def otorgar_logro_nivel_avanzado(usuario, entreno, quest_usuario):
        """
        Otorga logro cuando el usuario alcanza nivel 5 o superior
        """
        # Implementar la lógica que estaba en la línea 990
        pass

    def verificar_otros_logros(usuario, entreno, quest_usuario):
        """
        Verifica otros logros adicionales
        """
        # Otras verificaciones de logros
        pass

    @classmethod
    def obtener_notificaciones_no_leidas(cls, cliente):
        """Obtiene las notificaciones no leídas de un cliente"""
        from .models import Notificacion

        return Notificacion.objects.filter(
            cliente=cliente,
            leida=False
        ).order_by('-fecha')

    @classmethod
    def marcar_como_leida(cls, notificacion_id):
        """Marca una notificación como leída"""
        from .models import Notificacion

        try:
            notificacion = Notificacion.objects.get(id=notificacion_id)
            notificacion.leida = True
            notificacion.save()
            return True
        except Notificacion.DoesNotExist:
            return False


# ============================================================================
# MEJORAS PARA AGREGAR A TU services.py
# ============================================================================
# Copia y pega estas mejoras en tu archivo services.py existente

import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta

# Configurar logging específico para gamificación
logger = logging.getLogger('gamificacion')


# ============================================================================
# 1. MEJORA: PROCESAMIENTO AUTOMÁTICO CON SIGNALS
# ============================================================================

@receiver(post_save, sender='entrenos.EntrenoRealizado')
def procesar_gamificacion_automaticamente(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta automáticamente cada vez que se guarda un entrenamiento.
    Esta es la clave para que el sistema funcione automáticamente.
    """
    if created:  # Solo procesar entrenamientos nuevos
        logger.info(f"🎮 Procesando gamificación automáticamente para entreno {instance.id}")

        try:
            # Usar el servicio mejorado para procesar
            resultado = GamificacionServiceMejorado.procesar_entreno_completo(instance)

            if resultado:
                logger.info(
                    f"✅ Gamificación procesada: {resultado['logros_nuevos']} logros, {resultado['puntos_ganados']} puntos")
            else:
                logger.warning(f"⚠️ No se pudo procesar gamificación para entreno {instance.id}")

        except Exception as e:
            logger.error(f"❌ Error en procesamiento automático: {e}", exc_info=True)


# ============================================================================
# 2. MEJORA: SERVICIO DE GAMIFICACIÓN ROBUSTO Y TRANSACCIONAL
# ============================================================================

class GamificacionServiceMejorado:
    """
    Versión mejorada del servicio de gamificación con:
    - Transacciones atómicas
    - Logging comprehensivo
    - Manejo de errores robusto
    - Validación de integridad
    """

    @classmethod
    @transaction.atomic
    def procesar_entreno_completo(cls, entreno):
        """
        Procesa completamente un entrenamiento: puntos, logros, misiones, nivel.
        Usa transacciones atómicas para garantizar consistencia.
        """
        logger.info(f"🔄 Iniciando procesamiento completo para entreno {entreno.id}")

        try:
            # 1. Obtener o crear perfil (con lock para evitar condiciones de carrera)
            perfil, created = PerfilGamificacion.objects.select_for_update().get_or_create(
                cliente=entreno.cliente,
                defaults={
                    'nivel_actual': Nivel.objects.order_by('numero').first(),
                    'puntos_totales': 0,
                    'entrenos_totales': 0,
                    'racha_actual': 0,
                    'racha_maxima': 0
                }
            )

            if created:
                logger.info(f"✨ Perfil de gamificación creado para {entreno.cliente.nombre}")

            # 2. Actualizar estadísticas básicas
            puntos_actividad = cls._actualizar_estadisticas_base(perfil, entreno)

            # 3. Verificar y otorgar logros
            logros_nuevos = cls._verificar_y_otorgar_logros(perfil, entreno)

            # 4. Verificar y actualizar misiones
            misiones_completadas = cls._verificar_y_actualizar_misiones(perfil, entreno)

            # 5. Actualizar nivel si es necesario
            nivel_anterior = perfil.nivel_actual
            subio_nivel = perfil.actualizar_nivel()

            # 6. Guardar perfil una sola vez al final
            perfil.save()

            # 7. Crear notificaciones si es necesario
            if subio_nivel:
                cls._crear_notificacion_nivel(perfil, nivel_anterior)

            # 8. Validar integridad final
            cls._validar_integridad_perfil(perfil)

            resultado = {
                'perfil_id': perfil.id,
                'puntos_ganados': puntos_actividad,
                'logros_nuevos': len(logros_nuevos),
                'misiones_completadas': len(misiones_completadas),
                'subio_nivel': subio_nivel,
                'nivel_actual': perfil.nivel_actual.numero if perfil.nivel_actual else 1,
                'puntos_totales': perfil.puntos_totales
            }

            logger.info(f"✅ Procesamiento exitoso: {resultado}")
            return resultado

        except Exception as e:
            logger.error(f"❌ Error en procesamiento completo: {e}", exc_info=True)
            # La transacción se revierte automáticamente
            return None

    @classmethod
    def _actualizar_estadisticas_base(cls, perfil, entreno):
        """
        Actualiza contadores básicos y calcula puntos por actividad.
        NO guarda el perfil, solo modifica el objeto en memoria.
        """
        # Calcular puntos por actividad
        puntos_base = 100  # Puntos base por entrenar

        # Bonificaciones por métricas del entrenamiento
        if entreno.volumen_total_kg:
            puntos_base += int(entreno.volumen_total_kg / 20)

        if entreno.calorias_quemadas:
            puntos_base += int(entreno.calorias_quemadas / 10)

        # Bonificación por completar todas las series
        series_total = SerieRealizada.objects.filter(entreno=entreno).count()
        series_completadas = SerieRealizada.objects.filter(entreno=entreno, completado=True).count()

        if series_total > 0 and series_total == series_completadas:
            puntos_base += 50  # Bonus por completar todo

        # Actualizar perfil
        perfil.puntos_totales += puntos_base
        perfil.entrenos_totales += 1

        # Actualizar racha
        cls._actualizar_racha(perfil, entreno)

        # Registrar en historial
        HistorialPuntos.objects.create(
            perfil=perfil,
            puntos=puntos_base,
            descripcion=f"Entrenamiento completado: {entreno.fuente_datos}",
            fecha=timezone.now()
        )

        logger.info(
            f"📊 Estadísticas actualizadas: +{puntos_base} puntos, {perfil.entrenos_totales} entrenamientos totales")
        return puntos_base

    @classmethod
    def _actualizar_racha(cls, perfil, entreno):
        """Actualiza la racha de entrenamientos de forma robusta"""
        if perfil.fecha_ultimo_entreno:
            # Convertir a fecha si es datetime
            fecha_ultimo = perfil.fecha_ultimo_entreno
            if hasattr(fecha_ultimo, 'date'):
                fecha_ultimo = fecha_ultimo.date()

            fecha_entreno = entreno.fecha
            if hasattr(fecha_entreno, 'date'):
                fecha_entreno = fecha_entreno.date()

            dias_diff = (fecha_entreno - fecha_ultimo).days

            if dias_diff == 1:
                # Día consecutivo
                perfil.racha_actual += 1
                logger.info(f"🔥 Racha continuada: {perfil.racha_actual} días")
            elif dias_diff > 1:
                # Se rompió la racha
                logger.info(f"💔 Racha rota después de {perfil.racha_actual} días")
                perfil.racha_actual = 1
            # Si dias_diff <= 0, es el mismo día o anterior, no afecta la racha
        else:
            # Primer entrenamiento
            perfil.racha_actual = 1
            logger.info("🌟 Primera racha iniciada")

        # Actualizar racha máxima
        if perfil.racha_actual > perfil.racha_maxima:
            perfil.racha_maxima = perfil.racha_actual
            logger.info(f"🏆 Nueva racha máxima: {perfil.racha_maxima} días")

        perfil.fecha_ultimo_entreno = entreno.fecha

    @classmethod
    def _verificar_y_otorgar_logros(cls, perfil, entreno):
        """
        Verifica todos los logros y otorga los que se hayan desbloqueado.
        Retorna lista de logros nuevos.
        """
        logros_nuevos = []

        # Obtener logros que el usuario aún no ha completado
        logros_pendientes = Logro.objects.exclude(
            usuarios__perfil=perfil,
            usuarios__completado=True
        )

        logger.info(f"🎯 Verificando {logros_pendientes.count()} logros pendientes")

        for logro in logros_pendientes:
            try:
                # Calcular progreso actual para este logro
                progreso_actual = cls._calcular_progreso_logro(perfil, logro, entreno)

                # Obtener o crear LogroUsuario
                logro_usuario, created = LogroUsuario.objects.get_or_create(
                    perfil=perfil,
                    logro=logro,
                    defaults={
                        'progreso_actual': progreso_actual,
                        'completado': False
                    }
                )

                # Actualizar progreso
                logro_usuario.progreso_actual = progreso_actual

                # Verificar si se desbloqueó
                if progreso_actual >= logro.meta_valor and not logro_usuario.completado:
                    # ¡Logro desbloqueado!
                    logro_usuario.completado = True
                    logro_usuario.fecha_desbloqueo = timezone.now()
                    logro_usuario.save()

                    # Otorgar puntos
                    perfil.puntos_totales += logro.puntos_recompensa

                    # Registrar en historial
                    HistorialPuntos.objects.create(
                        perfil=perfil,
                        puntos=logro.puntos_recompensa,
                        logro=logro,
                        descripcion=f"Logro desbloqueado: {logro.nombre}",
                        fecha=timezone.now()
                    )

                    logros_nuevos.append(logro)
                    logger.info(f"🏆 LOGRO DESBLOQUEADO: {logro.nombre} (+{logro.puntos_recompensa} puntos)")

                else:
                    # Solo actualizar progreso
                    logro_usuario.save()

            except Exception as e:
                logger.error(f"❌ Error verificando logro {logro.nombre}: {e}")
                continue

        return logros_nuevos

    @classmethod
    def _calcular_progreso_logro(cls, perfil, logro, entreno):
        """
        Función COMPLETA que reconoce TODOS los logros de tu sistema.
        Versión actualizada que incluye todos los logros específicos.
        """
        nombre_logro = logro.nombre.lower()
        cliente_id = perfil.cliente_id

        try:
            # === LOGROS BÁSICOS DE ENTRENAMIENTOS ===
            if "liftin principiante" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fuente_datos='liftin'
                ).count()

            if "liftin intermedio" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fuente_datos='liftin'
                ).count()

            if "liftin avanzado" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fuente_datos='liftin'
                ).count()

            # === LOGROS DE EXPLORACIÓN ===
            if "aventurero del fitness" in nombre_logro:
                return SerieRealizada.objects.filter(
                    entreno__cliente_id=cliente_id,
                    completado=True
                ).values('ejercicio').distinct().count()

            if "explorador de rutinas" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).values('rutina').distinct().count()

            # === LOGROS DE CONSISTENCIA ===
            if "rutina establecida" in nombre_logro:
                fecha_limite = timezone.now().date() - timedelta(days=30)
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fecha__gte=fecha_limite
                ).count()

            if "entrenador de fin de semana" in nombre_logro:
                entrenos_weekend = 0
                for entreno_obj in EntrenoRealizado.objects.filter(cliente_id=cliente_id):
                    if entreno_obj.fecha.weekday() in [5, 6]:  # Sábado y Domingo
                        entrenos_weekend += 1
                return entrenos_weekend

            # === LOGROS DE SUPERACIÓN ===
            if "más allá del límite" in nombre_logro or "mas alla del limite" in nombre_logro:
                duracion_promedio = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    duracion_minutos__isnull=False
                ).aggregate(promedio=Avg('duracion_minutos'))['promedio'] or 60

                limite_superior = float(duracion_promedio) * 1.5
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    duracion_minutos__gte=limite_superior
                ).count()

            if "rompe barreras" in nombre_logro:
                entrenamientos_con_mejora = 0
                for entreno_obj in EntrenoRealizado.objects.filter(cliente_id=cliente_id).order_by('fecha'):
                    series_entreno = SerieRealizada.objects.filter(entreno=entreno_obj, completado=True)
                    for serie in series_entreno:
                        serie_anterior = SerieRealizada.objects.filter(
                            entreno__cliente_id=cliente_id,
                            ejercicio=serie.ejercicio,
                            entreno__fecha__lt=entreno_obj.fecha,
                            completado=True
                        ).order_by('-entreno__fecha').first()

                        if serie_anterior and serie.peso_kg > serie_anterior.peso_kg:
                            entrenamientos_con_mejora += 1
                            break
                return entrenamientos_con_mejora

            if "desafío aceptado" in nombre_logro or "desafio aceptado" in nombre_logro:
                volumen_promedio = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    volumen_total_kg__isnull=False
                ).aggregate(promedio=Avg('volumen_total_kg'))['promedio'] or 500

                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    volumen_total_kg__gte=float(volumen_promedio) * 1.2
                ).count()

            # === LOGROS DE CALORÍAS ===
            if "quemador principiante" in nombre_logro:
                total_calorias = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).aggregate(total=Sum('calorias_quemadas'))['total'] or 0
                return int(total_calorias)

            if "incinerador" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    calorias_quemadas__gte=800
                ).count()

            # === LOGROS DE DESARROLLO COMPLETO ===
            if "entrenamiento holístico" in nombre_logro or "entrenamiento holistico" in nombre_logro:
                return SerieRealizada.objects.filter(
                    entreno__cliente_id=cliente_id,
                    completado=True
                ).values('ejercicio__grupo_muscular').distinct().count()

            if "desarrollo completo" in nombre_logro:
                entrenamientos_completos = 0
                for entreno_obj in EntrenoRealizado.objects.filter(cliente_id=cliente_id):
                    grupos_en_entreno = SerieRealizada.objects.filter(
                        entreno=entreno_obj,
                        completado=True
                    ).values('ejercicio__grupo_muscular').distinct().count()

                    if grupos_en_entreno >= 3:
                        entrenamientos_completos += 1
                return entrenamientos_completos

            # === LOGROS SOCIALES ===
            if "inspirador" in nombre_logro:
                return perfil.entrenos_totales

            if "competidor amistoso" in nombre_logro:
                return cls._calcular_entrenamientos_perfectos(cliente_id)

            # === LOGROS DE TÉCNICA ===
            if "control total" in nombre_logro:
                return cls._calcular_entrenamientos_perfectos(cliente_id)

            if "precisión milimétrica" in nombre_logro or "precision milimetrica" in nombre_logro:
                entrenamientos_precisos = 0
                for entreno_obj in EntrenoRealizado.objects.filter(cliente_id=cliente_id):
                    ejercicios_en_entreno = SerieRealizada.objects.filter(
                        entreno=entreno_obj,
                        completado=True
                    ).values('ejercicio').distinct()

                    precision_en_entreno = True
                    for ejercicio_data in ejercicios_en_entreno:
                        ejercicio_id = ejercicio_data['ejercicio']
                        pesos_ejercicio = SerieRealizada.objects.filter(
                            entreno=entreno_obj,
                            ejercicio_id=ejercicio_id,
                            completado=True
                        ).values_list('peso_kg', flat=True)

                        if len(set(pesos_ejercicio)) > 1:
                            precision_en_entreno = False
                            break

                    if precision_en_entreno:
                        entrenamientos_precisos += 1
                return entrenamientos_precisos

            if "forma perfecta" in nombre_logro:
                return cls._calcular_entrenamientos_perfectos(cliente_id)

            # === LOGROS DE BIENESTAR ===
            if "nutrición óptima" in nombre_logro or "nutricion optima" in nombre_logro:
                fecha_limite = timezone.now().date() - timedelta(days=30)
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fecha__gte=fecha_limite
                ).count()

            if "hidratación perfecta" in nombre_logro or "hidratacion perfecta" in nombre_logro:
                return perfil.entrenos_totales

            # === LOGROS DE MAESTRÍA ===
            if "maestro" in nombre_logro:
                return perfil.entrenos_totales

            if "mentor del fitness" in nombre_logro:
                return perfil.entrenos_totales

            if "entrenamiento en equipo" in nombre_logro:
                return perfil.entrenos_totales

            # === LOGROS DE RACHA ===
            if "racha" in nombre_logro:
                return perfil.racha_actual

            # === LOGROS DE VOLUMEN ===
            if "volumen" in nombre_logro:
                total_volumen = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).aggregate(total=Sum('volumen_total_kg'))['total'] or 0
                return int(total_volumen)

            # === LOGROS ESPECIALES ===
            if "primer" in nombre_logro:
                return 1 if perfil.entrenos_totales >= 1 else 0

            if "consistencia" in nombre_logro or "constante" in nombre_logro:
                fecha_limite = timezone.now().date() - timedelta(days=30)
                return EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id,
                    fecha__gte=fecha_limite
                ).count()

            # Si no se reconoce el logro, devolver 0
            logger.warning(f"⚠️ Logro no reconocido: {logro.nombre}")
            return 0

        except Exception as e:
            logger.error(f"❌ Error calculando progreso para {logro.nombre}: {e}")
            return 0

    @classmethod
    def _verificar_y_actualizar_misiones(cls, perfil, entreno):
        """
        Verifica y actualiza misiones activas.
        Retorna lista de misiones completadas.
        """
        misiones_completadas = []

        # Por ahora, implementación básica
        # Puedes expandir esto según tus necesidades de misiones

        return misiones_completadas

    @classmethod
    def _crear_notificacion_nivel(cls, perfil, nivel_anterior):
        """Crea notificación cuando el usuario sube de nivel"""
        try:
            # Implementar según tu sistema de notificaciones
            logger.info(f"🎉 {perfil.cliente.nombre} subió al nivel {perfil.nivel_actual.numero}")
        except Exception as e:
            logger.error(f"❌ Error creando notificación de nivel: {e}")

    @classmethod
    def _validar_integridad_perfil(cls, perfil):
        """
        Valida que los datos del perfil sean consistentes.
        Útil para detectar problemas de sincronización.
        """
        try:
            # Validar que los puntos totales coincidan con el historial
            puntos_historial = HistorialPuntos.objects.filter(
                perfil=perfil
            ).aggregate(total=Sum('puntos'))['total'] or 0

            if abs(perfil.puntos_totales - puntos_historial) > 10:  # Tolerancia de 10 puntos
                logger.warning(
                    f"⚠️ Inconsistencia detectada en perfil {perfil.id}: "
                    f"Perfil={perfil.puntos_totales}, Historial={puntos_historial}"
                )

            # Validar que el número de entrenamientos sea consistente
            entrenos_reales = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente
            ).count()

            if perfil.entrenos_totales != entrenos_reales:
                logger.warning(
                    f"⚠️ Inconsistencia en entrenamientos para perfil {perfil.id}: "
                    f"Perfil={perfil.entrenos_totales}, Real={entrenos_reales}"
                )
                # Auto-corregir
                perfil.entrenos_totales = entrenos_reales

        except Exception as e:
            logger.error(f"❌ Error validando integridad: {e}")

    @classmethod
    def _calcular_entrenamientos_perfectos(cls, cliente_id):
        """
        Función auxiliar para calcular entrenamientos donde se completaron todas las series.
        """
        entrenamientos_perfectos = 0

        for entreno_obj in EntrenoRealizado.objects.filter(cliente_id=cliente_id):
            series_total = SerieRealizada.objects.filter(entreno=entreno_obj).count()
            series_completadas = SerieRealizada.objects.filter(
                entreno=entreno_obj,
                completado=True
            ).count()

            if series_total > 0 and series_total == series_completadas:
                entrenamientos_perfectos += 1

        return entrenamientos_perfectos


# ============================================================================
# 3. MEJORA: HERRAMIENTAS DE GESTIÓN Y DEBUGGING
# ============================================================================

class GamificacionDebugService:
    """
    Herramientas para debugging y gestión del sistema de gamificación.
    """

    @classmethod
    def diagnosticar_perfil(cls, cliente_id):
        """
        Realiza un diagnóstico completo de un perfil de gamificación.
        """
        try:
            perfil = PerfilGamificacion.objects.get(cliente_id=cliente_id)
        except PerfilGamificacion.DoesNotExist:
            return {"error": f"No existe perfil para cliente {cliente_id}"}

        # Calcular estadísticas reales
        entrenos_reales = EntrenoRealizado.objects.filter(cliente_id=cliente_id).count()
        puntos_historial = HistorialPuntos.objects.filter(perfil=perfil).aggregate(
            total=Sum('puntos')
        )['total'] or 0

        logros_completados = LogroUsuario.objects.filter(
            perfil=perfil,
            completado=True
        ).count()

        puntos_logros = LogroUsuario.objects.filter(
            perfil=perfil,
            completado=True
        ).aggregate(
            total=Sum('logro__puntos_recompensa')
        )['total'] or 0

        return {
            "perfil_id": perfil.id,
            "cliente": perfil.cliente.nombre,
            "entrenos_perfil": perfil.entrenos_totales,
            "entrenos_reales": entrenos_reales,
            "puntos_perfil": perfil.puntos_totales,
            "puntos_historial": puntos_historial,
            "puntos_logros": puntos_logros,
            "logros_completados": logros_completados,
            "racha_actual": perfil.racha_actual,
            "racha_maxima": perfil.racha_maxima,
            "nivel": perfil.nivel_actual.numero if perfil.nivel_actual else "Sin nivel",
            "inconsistencias": {
                "entrenos": perfil.entrenos_totales != entrenos_reales,
                "puntos": abs(perfil.puntos_totales - puntos_historial) > 10
            }
        }

    @classmethod
    def recalcular_perfil_completo(cls, cliente_id):
        """
        Recalcula completamente un perfil desde cero.
        Útil para corregir inconsistencias.
        """
        with transaction.atomic():
            try:
                perfil = PerfilGamificacion.objects.select_for_update().get(cliente_id=cliente_id)

                # Resetear contadores
                perfil.puntos_totales = 0
                perfil.entrenos_totales = 0
                perfil.racha_actual = 0
                perfil.racha_maxima = 0

                # Limpiar historial y logros
                HistorialPuntos.objects.filter(perfil=perfil).delete()
                LogroUsuario.objects.filter(perfil=perfil).update(
                    completado=False,
                    progreso_actual=0,
                    fecha_desbloqueo=None
                )

                # Reprocesar todos los entrenamientos
                entrenamientos = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).order_by('fecha')

                for entreno in entrenamientos:
                    GamificacionServiceMejorado.procesar_entreno_completo(entreno)

                return {"success": True, "entrenamientos_procesados": entrenamientos.count()}

            except Exception as e:
                logger.error(f"❌ Error recalculando perfil {cliente_id}: {e}")
                return {"error": str(e)}


# ============================================================================
# 4. MEJORA: CONFIGURACIÓN DE LOGGING
# ============================================================================

def configurar_logging_gamificacion():
    """
    Configura el logging específico para gamificación.
    Llama esta función en tu settings.py o apps.py
    """
    import logging

    # Crear logger específico para gamificación
    gamification_logger = logging.getLogger('gamificacion')
    gamification_logger.setLevel(logging.INFO)

    # Crear handler para archivo
    file_handler = logging.FileHandler('logs/gamificacion.log')
    file_handler.setLevel(logging.INFO)

    # Crear handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Crear formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Agregar handlers al logger
    gamification_logger.addHandler(file_handler)
    gamification_logger.addHandler(console_handler)

    return gamification_logger


# ============================================================================
# PASO 4: HERRAMIENTAS AVANZADAS DE DEBUGGING Y VALIDACIÓN
# ============================================================================
# Agrega estas herramientas a tu services.py para mantener el sistema robusto

import logging
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('gamificacion')


class GamificacionDebugService:
    """
    Servicio especializado en debugging y validación del sistema de gamificación.
    """

    @classmethod
    def diagnosticar_perfil_completo(cls, cliente_id):
        """
        Diagnóstico completo de un perfil de gamificación.
        Detecta inconsistencias y proporciona información detallada.
        """
        try:
            from logros.models import PerfilGamificacion, LogroUsuario, HistorialPuntos
            from entrenos.models import EntrenoRealizado

            logger.info(f"🔍 Iniciando diagnóstico completo para cliente {cliente_id}")

            # Obtener datos básicos
            perfil = PerfilGamificacion.objects.get(cliente_id=cliente_id)
            entrenos_reales = EntrenoRealizado.objects.filter(cliente_id=cliente_id).count()
            logros_completados = LogroUsuario.objects.filter(
                perfil=perfil,
                completado=True
            ).count()

            # Calcular puntos desde historial
            puntos_historial = HistorialPuntos.objects.filter(
                perfil=perfil
            ).aggregate(total=Sum('puntos'))['total'] or 0

            # Calcular puntos desde logros
            puntos_logros = LogroUsuario.objects.filter(
                perfil=perfil,
                completado=True
            ).aggregate(total=Sum('logro__puntos_recompensa'))['total'] or 0

            # Crear reporte de diagnóstico
            diagnostico = {
                'cliente_id': cliente_id,
                'perfil_id': perfil.id,
                'nivel_actual': perfil.nivell,
                'datos_perfil': {
                    'puntos_totales': perfil.puntos_totales,
                    'entrenos_totales': perfil.entrenos_totales,
                    'racha_actual': perfil.racha_actual,
                    'fecha_ultimo_entreno': perfil.fecha_ultimo_entreno,
                },
                'datos_reales': {
                    'entrenos_bd': entrenos_reales,
                    'logros_completados': logros_completados,
                    'puntos_historial': puntos_historial,
                    'puntos_logros': puntos_logros,
                },
                'inconsistencias': [],
                'recomendaciones': []
            }

            # Detectar inconsistencias
            if perfil.puntos_totales != puntos_historial:
                inconsistencia = {
                    'tipo': 'puntos_desincronizados',
                    'descripcion': f'Perfil: {perfil.puntos_totales}, Historial: {puntos_historial}',
                    'severidad': 'alta'
                }
                diagnostico['inconsistencias'].append(inconsistencia)
                diagnostico['recomendaciones'].append('Ejecutar sincronización de puntos')

            if perfil.entrenos_totales != entrenos_reales:
                inconsistencia = {
                    'tipo': 'entrenos_desincronizados',
                    'descripcion': f'Perfil: {perfil.entrenos_totales}, Real: {entrenos_reales}',
                    'severidad': 'media'
                }
                diagnostico['inconsistencias'].append(inconsistencia)
                diagnostico['recomendaciones'].append('Actualizar contador de entrenamientos')

            # Verificar logros potenciales
            logros_potenciales = cls._detectar_logros_potenciales(perfil)
            if logros_potenciales:
                diagnostico['logros_potenciales'] = logros_potenciales
                diagnostico['recomendaciones'].append('Procesar logros pendientes')

            # Estado general
            if not diagnostico['inconsistencias']:
                diagnostico['estado'] = 'saludable'
            elif len(diagnostico['inconsistencias']) <= 2:
                diagnostico['estado'] = 'necesita_atencion'
            else:
                diagnostico['estado'] = 'critico'

            logger.info(f"✅ Diagnóstico completado: {diagnostico['estado']}")
            return diagnostico

        except Exception as e:
            logger.error(f"❌ Error en diagnóstico completo: {e}")
            return {'error': str(e)}

    @classmethod
    def _detectar_logros_potenciales(cls, perfil):
        """
        Detecta logros que deberían estar completados pero no lo están.
        """
        from logros.models import Logro, LogroUsuario

        logros_potenciales = []
        logros_no_completados = Logro.objects.exclude(
            id__in=LogroUsuario.objects.filter(
                perfil=perfil,
                completado=True
            ).values_list('logro_id', flat=True)
        )

        for logro in logros_no_completados:
            try:
                # Usar la función de cálculo existente
                from logros.services import GamificacionServiceMejorado
                progreso = GamificacionServiceMejorado._calcular_progreso_logro(
                    perfil, logro, None
                )

                if progreso >= logro.meta_valor:
                    logros_potenciales.append({
                        'logro_id': logro.id,
                        'nombre': logro.nombre,
                        'progreso': progreso,
                        'meta': logro.meta_valor,
                        'puntos': logro.puntos_recompensa
                    })
            except Exception as e:
                logger.warning(f"Error evaluando logro {logro.nombre}: {e}")

        return logros_potenciales

    @classmethod
    def sincronizar_datos_perfil(cls, cliente_id):
        """
        Sincroniza todos los datos de un perfil para corregir inconsistencias.
        """
        try:
            with transaction.atomic():
                from logros.models import PerfilGamificacion, HistorialPuntos
                from entrenos.models import EntrenoRealizado

                logger.info(f"🔄 Sincronizando datos para cliente {cliente_id}")

                perfil = PerfilGamificacion.objects.get(cliente_id=cliente_id)

                # Recalcular puntos desde historial
                puntos_reales = HistorialPuntos.objects.filter(
                    perfil=perfil
                ).aggregate(total=Sum('puntos'))['total'] or 0

                # Recalcular entrenamientos
                entrenos_reales = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).count()

                # Actualizar perfil
                perfil.puntos_totales = puntos_reales
                perfil.entrenos_totales = entrenos_reales

                # Recalcular nivel
                perfil.nivel = cls._calcular_nivel_por_puntos(puntos_reales)

                # Actualizar fecha último entrenamiento
                ultimo_entreno = EntrenoRealizado.objects.filter(
                    cliente_id=cliente_id
                ).order_by('-fecha').first()

                if ultimo_entreno:
                    perfil.fecha_ultimo_entreno = ultimo_entreno.fecha

                perfil.save()

                logger.info(f"✅ Sincronización completada: {puntos_reales} puntos, {entrenos_reales} entrenamientos")

                return {
                    'exito': True,
                    'puntos_actualizados': puntos_reales,
                    'entrenos_actualizados': entrenos_reales,
                    'nivel_actualizado': perfil.nivel
                }

        except Exception as e:
            logger.error(f"❌ Error en sincronización: {e}")
            return {'exito': False, 'error': str(e)}

    @classmethod
    def _calcular_nivel_por_puntos(cls, puntos):
        """
        Calcula el nivel basado en los puntos totales.
        """
        if puntos < 1000:
            return 1
        elif puntos < 3000:
            return 2
        elif puntos < 6000:
            return 3
        elif puntos < 10000:
            return 4
        else:
            return 5

    @classmethod
    def procesar_logros_pendientes(cls, cliente_id):
        """
        Procesa y otorga logros que deberían estar completados.
        """
        try:
            with transaction.atomic():
                from logros.models import PerfilGamificacion
                from logros.services import GamificacionServiceMejorado

                logger.info(f"🎯 Procesando logros pendientes para cliente {cliente_id}")

                perfil = PerfilGamificacion.objects.get(cliente_id=cliente_id)

                # Detectar logros potenciales
                logros_potenciales = cls._detectar_logros_potenciales(perfil)

                logros_otorgados = []
                puntos_ganados = 0

                for logro_data in logros_potenciales:
                    resultado = GamificacionServiceMejorado._otorgar_logro(
                        perfil,
                        logro_data['logro_id']
                    )

                    if resultado['otorgado']:
                        logros_otorgados.append(logro_data['nombre'])
                        puntos_ganados += logro_data['puntos']
                        logger.info(f"🏆 Logro otorgado: {logro_data['nombre']} (+{logro_data['puntos']} puntos)")

                return {
                    'exito': True,
                    'logros_otorgados': logros_otorgados,
                    'puntos_ganados': puntos_ganados,
                    'total_logros': len(logros_otorgados)
                }

        except Exception as e:
            logger.error(f"❌ Error procesando logros pendientes: {e}")
            return {'exito': False, 'error': str(e)}

    @classmethod
    def validar_integridad_sistema(cls):
        """
        Valida la integridad de todo el sistema de gamificación.
        """
        try:
            from logros.models import PerfilGamificacion

            logger.info("🔍 Validando integridad del sistema completo")

            perfiles = PerfilGamificacion.objects.all()
            reporte = {
                'perfiles_analizados': perfiles.count(),
                'perfiles_saludables': 0,
                'perfiles_con_problemas': 0,
                'problemas_detectados': [],
                'recomendaciones_globales': []
            }

            for perfil in perfiles:
                diagnostico = cls.diagnosticar_perfil_completo(perfil.cliente_id)

                if diagnostico.get('estado') == 'saludable':
                    reporte['perfiles_saludables'] += 1
                else:
                    reporte['perfiles_con_problemas'] += 1
                    reporte['problemas_detectados'].append({
                        'cliente_id': perfil.cliente_id,
                        'problemas': diagnostico.get('inconsistencias', [])
                    })

            # Generar recomendaciones globales
            if reporte['perfiles_con_problemas'] > 0:
                reporte['recomendaciones_globales'].append('Ejecutar sincronización masiva')
                reporte['recomendaciones_globales'].append('Revisar configuración de signals')

            logger.info(
                f"✅ Validación completada: {reporte['perfiles_saludables']}/{reporte['perfiles_analizados']} perfiles saludables")

            return reporte

        except Exception as e:
            logger.error(f"❌ Error en validación de integridad: {e}")
            return {'error': str(e)}
