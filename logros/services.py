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

    # Solución Recomendada para services.py

    def verificar_logros(usuario, entreno):
        """
        Verifica y otorga logros basados en el entrenamiento del usuario.

        Args:
            usuario: Instancia del modelo Usuario
            entreno: Instancia del modelo Entreno
        """
        try:
            # SOLUCIÓN: Obtener quest_usuario de forma segura
            # Opción 1: Si es una relación ForeignKey o OneToOne
            quest_usuario = getattr(usuario, 'quest_usuario', None)

            # Opción 2: Si es una relación reversa (ManyToOne)
            if quest_usuario is None:
                quest_usuario = usuario.questusuario_set.first()

            # Opción 3: Si QuestUsuario es un modelo independiente
            if quest_usuario is None:
                from .models import QuestUsuario  # Asegurar importación
                quest_usuario = QuestUsuario.objects.filter(usuario=usuario).first()

            # Crear quest_usuario si no existe
            if quest_usuario is None:
                from .models import QuestUsuario
                quest_usuario = QuestUsuario.objects.create(
                    usuario=usuario,
                    nivel=1,
                    puntos=0
                )

            # LÍNEA 990: Verificación segura del nivel
            if quest_usuario and hasattr(quest_usuario, 'nivel') and quest_usuario.nivel >= 5:
                # Aquí va la lógica del logro que estaba en la línea 990
                otorgar_logro_nivel_avanzado(usuario, entreno, quest_usuario)

            # Otras verificaciones de logros...
            verificar_otros_logros(usuario, entreno, quest_usuario)

        except AttributeError as e:
            # Log del error para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error de atributo al verificar logros para usuario {usuario.id}: {e}")

        except Exception as e:
            # Manejo de otros errores
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error inesperado en verificar_logros para usuario {usuario.id}: {e}")

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
