# 🎯 VISTAS COMPLETAS DEL CENTRO DE ANÁLISIS - ADAPTADAS PARA TABLA EXISTENTE
# Archivo: analytics/views.py (VERSIÓN COMPLETA)
from django.shortcuts import render, get_object_or_404
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Avg, Max, Min, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from entrenos.utils import parsear_ejercicios
from clientes.models import Cliente
from entrenos.models import EntrenoRealizado, EjercicioLiftinDetallado
from .models import (
    MetricaRendimiento, AnalisisEjercicio, TendenciaProgresion,
    PrediccionRendimiento, RecomendacionEntrenamiento, ComparativaRendimiento
)

from entrenos.models import EntrenoRealizado, EjercicioRealizado



class CalculadoraEjerciciosTabla:
    """
    Calculadora que usa los datos de la tabla estructurada EjercicioRealizado
    """

    def __init__(self, cliente):
        self.cliente = cliente

    # Archivo: analytics/views.py

    # ... (dentro de la clase CalculadoraEjerciciosTabla)
    def _metricas_vacias(self):
        """Retorna un diccionario de métricas con valores en cero."""
        return {
            'volumen_total': 0,
            'intensidad_promedio': 0,
            'calorias_totales': 0,
            'frecuencia_semanal': 0,
            'duracion_promedio': 0,
            'consistencia': 0,
            'total_ejercicios': 0,
            'ejercicios_unicos': 0,
            'peso_promedio': 0,
            'peso_maximo': 0,
            'series_totales': 0,
            'repeticiones_totales': 0,
            'entrenamientos_unicos': 0
        }

    def obtener_ejercicios_tabla(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene todos los ejercicios realizados por el cliente con una consulta
        única y optimizada, asegurando que los filtros de fecha se apliquen correctamente.
        """
        # 1. Construir la consulta base sobre EjercicioRealizado
        # Usamos 'entreno__cliente' para filtrar por el cliente a través de la relación inversa.
        query = EjercicioRealizado.objects.filter(entreno__cliente=self.cliente)

        # 2. Aplicar los filtros de fecha directamente sobre el campo 'fecha' del entreno relacionado.
        if fecha_inicio:
            query = query.filter(entreno__fecha__gte=fecha_inicio)
        if fecha_fin:
            query = query.filter(entreno__fecha__lte=fecha_fin)

        # 3. Usar select_related para optimizar la consulta.
        # Esto precarga los datos del 'entreno' relacionado en la misma consulta,
        # evitando consultas adicionales a la base de datos dentro de un bucle.
        # También seleccionamos solo los campos que necesitamos con .values()
        ejercicios_qs = query.select_related('entreno').values(
            'nombre_ejercicio',
            'grupo_muscular',
            'peso_kg',
            'series',
            'repeticiones',
            'completado',
            'entreno__fecha',  # Obtenemos la fecha del entreno relacionado
            'entreno__id'
        )

        # 4. Construir la lista de diccionarios final.
        # Este paso es ahora mucho más rápido y los datos son más fiables.
        ejercicios = [
            {
                'nombre': e['nombre_ejercicio'],
                'grupo': e['grupo_muscular'],
                'peso': e['peso_kg'] or 0,
                'series': e['series'] or 1,
                'repeticiones': e['repeticiones'] or 1,
                'completado': bool(e['completado']),
                'fecha': e['entreno__fecha'],
                'cliente': self.cliente.nombre,
                'entreno_id': e['entreno__id']
            }
            for e in ejercicios_qs
        ]

        return ejercicios

    # Archivo: analytics/views.py

    # ... (dentro de la clase CalculadoraEjerciciosTabla)

    def calcular_metricas_principales(self, fecha_inicio=None, fecha_fin=None):
        """
        Calcula todas las métricas principales de forma consistente y eficiente,
        priorizando los datos pre-calculados del modelo EntrenoRealizado.
        """
        # 1. Obtener los entrenamientos del período con una única consulta.
        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )

        if not entrenamientos.exists():
            return self._metricas_vacias()

        # 2. Usar funciones de agregación de Django para obtener los totales.
        # Esto es mucho más eficiente que iterar en Python.
        agregados = entrenamientos.aggregate(
            volumen_total_agregado=Sum('volumen_total_kg'),
            duracion_total_agregada=Sum('duracion_minutos'),
            calorias_totales_agregadas=Sum('calorias_quemadas'),
            num_entrenamientos=Count('id')
        )

        # Asignar valores, manejando el caso de que no haya datos (None).
        volumen_total = agregados['volumen_total_agregado'] or 0
        duracion_total = agregados['duracion_total_agregada'] or 0
        calorias_totales = agregados['calorias_totales_agregadas'] or 0
        entrenamientos_unicos = agregados['num_entrenamientos']

        # 3. Calcular métricas derivadas.
        intensidad_promedio = (volumen_total / duracion_total) if duracion_total > 0 else 0
        duracion_promedio = (duracion_total / entrenamientos_unicos) if entrenamientos_unicos > 0 else 0

        dias_periodo = (fecha_fin - fecha_inicio).days + 1
        frecuencia_semanal = (entrenamientos_unicos * 7) / dias_periodo if dias_periodo > 0 else 0

        # 4. Para métricas a nivel de ejercicio (consistencia, peso máx, etc.),
        # necesitamos consultar la tabla de ejercicios.
        ejercicios = self.obtener_ejercicios_tabla(fecha_inicio, fecha_fin)
        total_ejercicios = len(ejercicios)
        ejercicios_completados = len([e for e in ejercicios if e.get('completado', False)])
        consistencia = (ejercicios_completados / total_ejercicios * 100) if total_ejercicios > 0 else 0

        pesos = [float(e['peso']) for e in ejercicios if isinstance(e.get('peso'), (int, float)) and e.get('peso') > 0]
        peso_maximo = max(pesos) if pesos else 0
        peso_promedio = sum(pesos) / len(pesos) if pesos else 0

        # 5. Devolver el diccionario completo con valores consistentes.
        return {
            'volumen_total': volumen_total,
            'intensidad_promedio': intensidad_promedio,
            'calorias_totales': calorias_totales,
            'frecuencia_semanal': frecuencia_semanal,
            'duracion_promedio': duracion_promedio,
            'consistencia': consistencia,
            'total_ejercicios': total_ejercicios,
            'ejercicios_unicos': len(set(e['nombre'] for e in ejercicios)),
            'peso_promedio': peso_promedio,
            'peso_maximo': peso_maximo,
            'series_totales': sum(e.get('series', 1) for e in ejercicios),
            'repeticiones_totales': sum(e.get('series', 1) * e.get('repeticiones', 1) for e in ejercicios),
            'entrenamientos_unicos': entrenamientos_unicos
        }

    # Archivo: analytics/views.py
    # Dentro de la clase CalculadoraEjerciciosTabla

    def obtener_ejercicios_progresion(self, limite=5, datos_ejercicios=None):
        """
        Calcula la progresión de peso para cada ejercicio.
        - Acepta una lista de ejercicios pre-cargada para evitar consultas extra.
        - Puede devolver todos los resultados si limite es None.
        - Calcula tanto progresiones positivas como negativas/estancadas.
        """
        # Si no se proporciona una lista de ejercicios, la obtiene de la base de datos.
        # Esto mantiene la compatibilidad con otras partes de tu código que puedan llamarla sin parámetros.
        ejercicios = datos_ejercicios if datos_ejercicios is not None else self.obtener_ejercicios_tabla()

        # Agrupar todos los registros de ejercicio por su nombre normalizado (insensible a mayúsculas)
        ejercicios_por_nombre = {}
        for e in ejercicios:
            nombre_normalizado = e['nombre'].strip().lower()
            nombre_mostrado = e['nombre'].strip().title()

            if nombre_normalizado not in ejercicios_por_nombre:
                ejercicios_por_nombre[nombre_normalizado] = {
                    'nombre_mostrado': nombre_mostrado,
                    'ejercicios': []
                }
            ejercicios_por_nombre[nombre_normalizado]['ejercicios'].append(e)

        progresiones = []
        for datos in ejercicios_por_nombre.values():
            lista_ejercicios = datos['ejercicios']
            nombre_mostrado = datos['nombre_mostrado']

            # Se necesitan al menos dos sesiones para calcular una progresión
            if len(lista_ejercicios) < 2:
                continue

            # Ordenar las sesiones por fecha para encontrar la primera y la última
            lista_ejercicios.sort(key=lambda x: x['fecha'])

            primero = lista_ejercicios[0]
            ultimo = lista_ejercicios[-1]

            try:
                # Obtener pesos, tratando 'PC' (Peso Corporal) como 0 para el cálculo de progresión
                peso_inicial = float(primero.get('peso', 0)) if primero.get('peso') != 'PC' else 0
                peso_final = float(ultimo.get('peso', 0)) if ultimo.get('peso') != 'PC' else 0

                # Solo calculamos el porcentaje si el peso inicial era mayor que cero
                if peso_inicial > 0:
                    progresion_peso = ((peso_final - peso_inicial) / peso_inicial) * 100
                else:
                    # Si empezamos en 0 y subimos, es un progreso, pero no podemos dividir por cero.
                    # Podríamos asignarle un valor simbólico o simplemente 0.
                    progresion_peso = 100.0 if peso_final > 0 else 0.0

                # ✅ CAMBIO: Ya no filtramos por progresion_peso > 0. Guardamos todos los resultados.
                progresiones.append({
                    'nombre_ejercicio': nombre_mostrado,
                    'progresion_peso': progresion_peso,
                    'peso_inicial': peso_inicial,
                    'peso_final': peso_final,
                    'sesiones': len(lista_ejercicios)
                })

            except (ValueError, TypeError):
                # Si hay algún error en la conversión de datos, se omite ese ejercicio.
                continue

        # El print de depuración se ha eliminado para no ensuciar la consola.
        # Puedes volver a añadirlo si necesitas depurar algo específico.

        # ✅ CAMBIO: La lógica del límite se aplica al final.
        if limite is not None:
            # Ordenar por el valor de la progresión para devolver los "mejores"
            progresiones.sort(key=lambda x: x['progresion_peso'], reverse=True)
            return progresiones[:limite]
        else:
            # Si no hay límite, devuelve todos los resultados sin un orden específico
            return progresiones

    def obtener_datos_graficos(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene datos para gráficos usando el campo de volumen pre-calculado
        del modelo EntrenoRealizado para garantizar la consistencia.
        """
        # 1. Construir la consulta base sobre EntrenoRealizado.
        query = EntrenoRealizado.objects.filter(cliente=self.cliente)

        # 2. Aplicar los filtros de fecha.
        if fecha_inicio:
            query = query.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            query = query.filter(fecha__lte=fecha_fin)

        # 3. Seleccionar solo los campos necesarios y ordenar por fecha.
        # Nos interesa la fecha y el volumen total que ya está guardado.
        entrenos_con_volumen = query.order_by('fecha').values('fecha', 'volumen_total_kg')

        # 4. Formatear los datos para el gráfico.
        # No hay necesidad de calcular nada, solo formatear.
        datos_volumen = [
            {
                'fecha': entreno['fecha'].strftime('%Y-%m-%d'),
                'volumen_total': entreno['volumen_total_kg'] or 0
            }
            for entreno in entrenos_con_volumen if entreno['volumen_total_kg'] is not None
        ]

        # El cálculo de intensidad ahora también usará el volumen correcto.
        datos_intensidad = []
        for item in datos_volumen:
            # Asume una duración de 60 min por sesión si no hay datos más precisos.
            intensidad = item['volumen_total'] / 60
            datos_intensidad.append({
                'fecha': item['fecha'],
                'intensidad_promedio': intensidad
            })

        return {
            'volumen_diario': datos_volumen,
            'intensidad_diaria': datos_intensidad
        }


from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
import json
from .models import RecomendacionEntrenamiento
from entrenos.models import EntrenoRealizado
from clientes.models import Cliente

from datetime import datetime  # Asegúrate de que datetime esté importado

# Archivo: analytics/views.py

# ... (tus imports)
  # Asegúrate de que esté importado


@login_required
def dashboard(request, cliente_id=None):
    from .analisis_progresion import AnalisisProgresionAvanzado
    """
    Dashboard principal del centro de análisis con todas las mejoras implementadas.
    """
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        cliente = Cliente.objects.first()
        if not cliente:
            return render(request, 'analytics/no_data.html')

    # --- 1. GESTIÓN DE FECHAS ---
    try:
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        fecha_inicio_actual = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin_actual = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        fecha_fin_actual = timezone.now().date()
        fecha_inicio_actual = fecha_fin_actual - timedelta(days=30)

    duracion_periodo_dias = (fecha_fin_actual - fecha_inicio_actual).days
    fecha_fin_anterior = fecha_inicio_actual - timedelta(days=1)
    fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=duracion_periodo_dias)

    # --- 2. CÁLCULO DE MÉTRICAS Y COMPARATIVAS ---
    calculadora = CalculadoraEjerciciosTabla(cliente)
    metricas_actuales = calculadora.calcular_metricas_principales(fecha_inicio_actual, fecha_fin_actual)
    metricas_anteriores = calculadora.calcular_metricas_principales(fecha_inicio_anterior, fecha_fin_anterior)

    comparativas = {}
    metricas_a_comparar = ['volumen_total', 'intensidad_promedio', 'calorias_totales', 'frecuencia_semanal',
                           'duracion_promedio', 'consistencia']
    for metrica in metricas_a_comparar:
        actual = metricas_actuales.get(metrica, 0)
        anterior = metricas_anteriores.get(metrica, 0)
        diferencia_pct = ((actual - anterior) / anterior * 100) if anterior > 0 else (100.0 if actual > 0 else 0.0)
        comparativas[metrica] = {'actual': actual, 'anterior': anterior, 'diferencia_pct': diferencia_pct}

    # --- 3. OBTENCIÓN DE DATOS PARA EL DASHBOARD ---

    # Datos generales
    entrenamientos_recientes = EntrenoRealizado.objects.filter(cliente=cliente, fecha__gte=fecha_inicio_actual,
                                                               fecha__lte=fecha_fin_actual).order_by('-fecha')[:10]
    recomendaciones = RecomendacionEntrenamiento.objects.filter(cliente=cliente, expires_at__gt=timezone.now(),
                                                                aplicada=False).order_by('prioridad')[:5]
    datos_graficos = calculadora.obtener_datos_graficos(fecha_inicio_actual, fecha_fin_actual)

    # Análisis de Estado del Atleta
    try:
        analizador_intensidad = AnalisisIntensidadAvanzado(cliente)
        estado_atleta = analizador_intensidad.calcular_fatiga_acumulada(periodo_dias=14)
    except Exception as e:
        print(f"Error al calcular el estado del atleta: {e}")
        estado_atleta = None

    # Análisis detallado de Ejercicios
    ejercicios_del_periodo = calculadora.obtener_ejercicios_tabla(fecha_inicio_actual, fecha_fin_actual)
    todos_los_ejercicios = calculadora.obtener_ejercicios_tabla()  # Para una progresión más completa

    progresiones = calculadora.obtener_ejercicios_progresion(limite=None, datos_ejercicios=todos_los_ejercicios)
    ejercicios_mejor_progresion = sorted([p for p in progresiones if p['progresion_peso'] > 0],
                                         key=lambda x: x['progresion_peso'], reverse=True)[:5]
    ejercicios_estancados = sorted([p for p in progresiones if p['progresion_peso'] <= 5],
                                   key=lambda x: x['progresion_peso'])[:5]

    # Cálculo de Frecuencia de Ejercicios con porcentaje para la barra visual
    frecuencia = {}
    for ej in ejercicios_del_periodo:
        nombre = ej['nombre'].strip().title()
        frecuencia[nombre] = frecuencia.get(nombre, 0) + 1

    ejercicios_mas_frecuentes_raw = sorted(frecuencia.items(), key=lambda x: x[1], reverse=True)[:5]
    max_frecuencia = ejercicios_mas_frecuentes_raw[0][1] if ejercicios_mas_frecuentes_raw else 0

    ejercicios_mas_frecuentes = []
    for nombre, count in ejercicios_mas_frecuentes_raw:
        porcentaje = (count / max_frecuencia * 100) if max_frecuencia > 0 else 0
        ejercicios_mas_frecuentes.append(
            {'nombre_ejercicio': nombre, 'sesiones': count, 'porcentaje_frecuencia': porcentaje})

    # --- 4. CONSTRUCCIÓN DEL CONTEXTO FINAL ---
    context = {
        'cliente': cliente,
        'metricas_principales': metricas_actuales,
        'comparativas': comparativas,
        'entrenamientos_recientes': entrenamientos_recientes,
        'recomendaciones': recomendaciones,
        'datos_volumen': json.dumps(datos_graficos['volumen_diario'], default=str),
        'datos_intensidad': json.dumps(datos_graficos['intensidad_diaria'], default=str),
        'fecha_inicio': fecha_inicio_actual.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin_actual.strftime('%Y-%m-%d'),
        'volumen_vacio': not datos_graficos['volumen_diario'],
        'intensidad_vacia': not datos_graficos['intensidad_diaria'],
        'estado_atleta': estado_atleta,
        'ejercicios_mejor_progresion': ejercicios_mejor_progresion,
        'ejercicios_estancados': ejercicios_estancados,
        'ejercicios_mas_frecuentes': ejercicios_mas_frecuentes,
        'ejercicios': ejercicios_del_periodo[:20],  # Para la tabla inferior, si aún la usas
    }

    return render(request, 'analytics/dashboard.html', context)


# Archivo: analytics/views.py

# Archivo: analytics/views.py

# ... (tus otros imports)
from django.shortcuts import render, get_object_or_404
from .models import TendenciaProgresion, PrediccionRendimiento
from .utils import parse_reps  # Asumiendo que tienes esta función en analytics/utils.py
import json


@login_required
def analisis_progresion(request, cliente_id):
    """
    Análisis detallado de progresión por ejercicio.
    Muestra gráfico, estadísticas, 1RM estimado, predicciones e historial de sesiones.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)
    todos_ejercicios = calculadora.obtener_ejercicios_tabla()

    # 1. Agrupar todos los ejercicios por nombre para el selector y el análisis
    ejercicios_dict = {}
    for e in todos_ejercicios:
        clave = e['nombre'].strip().lower()
        if clave not in ejercicios_dict:
            ejercicios_dict[clave] = {
                'nombre_mostrado': e['nombre'].strip().title(),
                'ejercicios': []
            }
        ejercicios_dict[clave]['ejercicios'].append(e)

    ejercicios_unicos = sorted([v['nombre_mostrado'] for v in ejercicios_dict.values()])

    # 2. Determinar el ejercicio seleccionado desde la URL o tomar el primero
    raw_nombre = request.GET.get('ejercicio')
    ejercicio_seleccionado = raw_nombre.strip().title() if raw_nombre else (
        ejercicios_unicos[0] if ejercicios_unicos else None)

    # 3. Inicializar todas las variables que se pasarán al contexto
    datos_progresion = []
    historial_ejercicio = []
    tendencia = None
    predicciones = []
    fila_1rm = None

    if ejercicio_seleccionado:
        # 4. Filtrar datos para el ejercicio seleccionado
        clave_seleccionada = ejercicio_seleccionado.lower()
        ejercicios_filtrados = ejercicios_dict.get(clave_seleccionada, {}).get('ejercicios', [])

        if ejercicios_filtrados:
            # Ordenar por fecha para el gráfico
            ejercicios_filtrados.sort(key=lambda x: x['fecha'])

            # Preparar el historial para la tabla (ordenado de más reciente a más antiguo)
            historial_ejercicio = sorted(ejercicios_filtrados, key=lambda x: x['fecha'], reverse=True)

            # Preparar datos para el gráfico
            for e in ejercicios_filtrados:
                try:
                    peso = float(e.get('peso', 0)) if e.get('peso') != 'PC' else 0
                    # Usamos str() para asegurar que el valor sea un string antes de parsear
                    series, reps = parse_reps(str(e.get('repeticiones', '1x1')))
                    if peso > 0:
                        datos_progresion.append({
                            'fecha': e['fecha'].strftime('%Y-%m-%d'),
                            'peso': peso,
                            'series': series,
                            'repeticiones': reps,
                            'volumen': peso * series * reps
                        })
                except (ValueError, TypeError):
                    continue

            # 5. Obtener datos de modelos de análisis relacionados
            tendencia = TendenciaProgresion.objects.filter(cliente=cliente,
                                                           nombre_ejercicio__iexact=ejercicio_seleccionado).order_by(
                '-fecha_fin').first()
            predicciones = PrediccionRendimiento.objects.filter(cliente=cliente,
                                                                nombre_ejercicio__iexact=ejercicio_seleccionado,
                                                                activa=True).order_by('-fecha_prediccion')[:3]

    # 6. Calcular la tabla de 1RM para todos los ejercicios y luego filtrar
    tabla_1rm_completa = []
    for datos in ejercicios_dict.values():
        lista = datos['ejercicios']
        nombre = datos['nombre_mostrado']
        entrenos_validos = []
        for e in lista:
            try:
                peso = float(e['peso']) if e.get('peso') != 'PC' else 0
                series, reps = parse_reps(str(e.get('repeticiones', '1x1')))
                if peso > 0 and reps > 0:
                    # Fórmula de Epley para 1RM: peso * (1 + reps / 30)
                    rm = round(peso * (1 + reps / 30), 2)
                    entrenos_validos.append({'fecha': e['fecha'], '1rm': rm})
            except (ValueError, TypeError):
                continue

        if len(entrenos_validos) >= 2:
            entrenos_validos.sort(key=lambda x: x['fecha'])
            rm_actual = entrenos_validos[-1]['1rm']
            rm_anterior = entrenos_validos[-2]['1rm']
            progreso = round(((rm_actual - rm_anterior) / rm_anterior) * 100, 2) if rm_anterior > 0 else 100.0
            tabla_1rm_completa.append(
                {'nombre': nombre, 'rm_actual': rm_actual, 'rm_anterior': rm_anterior, 'progreso': progreso})

    # Filtrar la fila del 1RM para el ejercicio seleccionado
    if ejercicio_seleccionado and tabla_1rm_completa:
        fila_1rm = next(
            (fila for fila in tabla_1rm_completa if fila['nombre'].lower() == ejercicio_seleccionado.lower()), None)

    # 7. Construir el contexto final para la plantilla
    context = {
        'cliente': cliente,
        'ejercicios': ejercicios_unicos,
        'ejercicio_seleccionado': ejercicio_seleccionado,
        'datos_progresion': json.dumps(datos_progresion, default=str),
        'tendencia': tendencia,
        'predicciones': predicciones,
        'tabla_1rm': fila_1rm,
        'historial_ejercicio': historial_ejercicio,
    }

    return render(request, 'analytics/progresion.html', context)


# Archivo: analytics/views.py

@login_required
def comparativas(request, cliente_id):
    """
    Análisis comparativo con TRES opciones:
    1. Temporal (vs período anterior)
    2. Por Grupo Muscular (agregado)
    3. Por Ejercicio (individual)
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    # --- 1. OBTENER PARÁMETROS Y CALCULAR FECHAS ---
    tipo_comparativa = request.GET.get('tipo', 'temporal')
    periodo_dias = int(request.GET.get('periodo', 30))

    fecha_fin_actual = timezone.now().date()
    fecha_inicio_actual = fecha_fin_actual - timedelta(days=periodo_dias)
    fecha_fin_anterior = fecha_inicio_actual - timedelta(days=1)
    fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=periodo_dias)

    # --- 2. LÓGICA DE COMPARACIÓN ---
    comparativas_data = {}  # Usaremos un diccionario para los tipos 'temporal' y 'ejercicio'

    if tipo_comparativa == 'temporal':
        # ... (esta lógica no cambia) ...
        metricas_actuales = calculadora.calcular_metricas_principales(fecha_inicio_actual, fecha_fin_actual)
        metricas_anteriores = calculadora.calcular_metricas_principales(fecha_inicio_anterior, fecha_fin_anterior)

        temp_data_list = []
        metricas_a_comparar = [
            ('volumen_total', 'Volumen Total'), ('intensidad_promedio', 'Intensidad Promedio'),
            ('calorias_totales', 'Calorías Totales'), ('consistencia', 'Consistencia')
        ]
        for clave, etiqueta in metricas_a_comparar:
            actual = metricas_actuales.get(clave, 0)
            anterior = metricas_anteriores.get(clave, 0)
            diferencia_pct = ((actual - anterior) / anterior * 100) if anterior > 0 else (100.0 if actual > 0 else 0.0)
            temp_data_list.append({
                'etiqueta': etiqueta, 'actual': actual, 'anterior': anterior,
                'diferencia_pct': diferencia_pct, 'diferencia_abs': actual - anterior,
            })
        comparativas_data = temp_data_list

    elif tipo_comparativa == 'grupo_muscular':
        # ... (esta lógica no cambia) ...
        ejercicios = calculadora.obtener_ejercicios_tabla(fecha_inicio_actual, fecha_fin_actual)
        volumen_por_grupo = {}
        for e in ejercicios:
            grupo = e.get('grupo', 'Otro').strip().title()
            if not grupo: continue
            try:
                peso = float(e.get('peso', 0));
                series = int(e.get('series', 1));
                reps = int(e.get('repeticiones', 1))
                volumen_por_grupo[grupo] = volumen_por_grupo.get(grupo, 0) + (peso * series * reps)
            except (ValueError, TypeError):
                continue

        volumen_ordenado = sorted(volumen_por_grupo.items(), key=lambda x: x[1], reverse=True)
        comparativas_data = [{'grupo': grupo, 'volumen': volumen} for grupo, volumen in volumen_ordenado]

    elif tipo_comparativa == 'ejercicio':
        # ✅ REINTRODUCIMOS LA LÓGICA ORIGINAL DE COMPARATIVA POR EJERCICIO
        ejercicios = calculadora.obtener_ejercicios_tabla(fecha_inicio_actual, fecha_fin_actual)

        ejercicios_metricas = {}
        for e in ejercicios:
            nombre_mostrado = e['nombre'].strip().title()
            if nombre_mostrado not in ejercicios_metricas:
                ejercicios_metricas[nombre_mostrado] = {'total_sesiones': 0, 'volumen_total': 0, 'peso_maximo': 0,
                                                        'pesos': []}

            try:
                peso = float(e.get('peso', 0))
                series = int(e.get('series', 1))
                reps = int(e.get('repeticiones', 1))

                ejercicios_metricas[nombre_mostrado]['total_sesiones'] += 1
                ejercicios_metricas[nombre_mostrado]['volumen_total'] += peso * series * reps
                ejercicios_metricas[nombre_mostrado]['peso_maximo'] = max(
                    ejercicios_metricas[nombre_mostrado]['peso_maximo'], peso)
                if peso > 0:
                    ejercicios_metricas[nombre_mostrado]['pesos'].append(peso)
            except (ValueError, TypeError):
                continue

        # Calcular promedios y ordenar
        for nombre, datos in ejercicios_metricas.items():
            pesos = datos['pesos']
            datos['peso_promedio'] = sum(pesos) / len(pesos) if pesos else 0
            del datos['pesos']  # Limpiamos la lista de pesos que ya no necesitamos

        # Ordenamos el diccionario por volumen total descendente
        comparativas_data = dict(
            sorted(ejercicios_metricas.items(), key=lambda item: item[1]['volumen_total'], reverse=True))

    # --- 3. CONSTRUCCIÓN DEL CONTEXTO ---
    context = {
        'cliente': cliente,
        'tipo_comparativa': tipo_comparativa,
        'periodo_seleccionado': periodo_dias,
        'comparativas_data': comparativas_data,
        'fecha_inicio_actual': fecha_inicio_actual.strftime('%d/%m/%Y'),
        'fecha_fin_actual': fecha_fin_actual.strftime('%d/%m/%Y'),
        'fecha_inicio_anterior': fecha_inicio_anterior.strftime('%d/%m/%Y'),
        'fecha_fin_anterior': fecha_fin_anterior.strftime('%d/%m/%Y'),
    }

    return render(request, 'analytics/comparativas.html', context)


@login_required
def recomendaciones(request, cliente_id):
    """
    Sistema de recomendaciones personalizadas
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Mapeo de prioridad textual a numérica
    PRIORIDADES = {'alta': 1, 'media': 2, 'baja': 3}

    # Obtener recomendaciones activas
    recomendaciones_activas = RecomendacionEntrenamiento.objects.filter(
        cliente=cliente,
        expires_at__gt=timezone.now()
    ).order_by('prioridad', '-created_at')

    # Obtener recomendaciones aplicadas recientes
    recomendaciones_aplicadas = RecomendacionEntrenamiento.objects.filter(
        cliente=cliente,
        aplicada=True,
        fecha_aplicacion__gte=timezone.now() - timedelta(days=30)
    ).order_by('-fecha_aplicacion')

    # Generar nuevas recomendaciones automáticas basadas en datos de la tabla
    calculadora = CalculadoraEjerciciosTabla(cliente)
    ejercicios = calculadora.obtener_ejercicios_tabla()
    ejercicios = calculadora.obtener_ejercicios_tabla()


    recomendaciones_automaticas = []

    # Análisis de consistencia
    if ejercicios:
        ejercicios_completados = len([e for e in ejercicios if e.get('completado', False)])
        consistencia = (ejercicios_completados / len(ejercicios)) * 100

        if consistencia < 70:
            recomendaciones_automaticas.append({
                'titulo': 'Mejorar Consistencia',
                'descripcion': f'Tu consistencia actual es del {consistencia:.1f}%. Intenta completar más ejercicios.',
                'tipo': 'consistencia',
                'prioridad': PRIORIDADES['alta']
            })

    # Análisis de progresión
    progresiones = calculadora.obtener_ejercicios_progresion(10)
    # print("🧪 Progresiones:", progresiones)

    ejercicios_estancados = []

    for prog in progresiones:
        if prog['progresion_peso'] < 5:
            nombre_normalizado = prog['nombre_ejercicio'].strip().title()
            ejercicios_estancados.append(nombre_normalizado)

    # Evitar duplicados con diferentes mayúsculas
    ejercicios_estancados = list(set(ejercicios_estancados))

    if ejercicios_estancados:
        recomendaciones_automaticas.append({
            'titulo': 'Ejercicios Estancados Detectados',
            'descripcion': f'Los ejercicios {", ".join(ejercicios_estancados[:3])} muestran poca progresión.',
            'tipo': 'progresion',
            'prioridad': PRIORIDADES['media']
        })

    # Crear recomendaciones en la base de datos si se presionó el botón
    mensaje = None
    if request.method == 'POST' and 'generar' in request.POST:
        for rec in recomendaciones_automaticas:
            RecomendacionEntrenamiento.objects.create(
                cliente=cliente,
                titulo=rec['titulo'],
                descripcion=rec['descripcion'],
                tipo=rec['tipo'],
                prioridad=rec['prioridad'],
                expires_at=timezone.now() + timedelta(days=30)
            )

        mensaje = f"Se generaron {len(recomendaciones_automaticas)} nuevas recomendaciones."

    context = {
        'cliente': cliente,
        'recomendaciones_activas': recomendaciones_activas,
        'recomendaciones_aplicadas': recomendaciones_aplicadas,
        'recomendaciones_automaticas': recomendaciones_automaticas,
        'mensaje': mensaje,
    }


    return render(request, 'analytics/recomendaciones.html', context)

    # Generar nuevas recomendaciones si es necesario
    mensaje = None
    if request.method == 'POST' and 'generar' in request.POST:
        # Crear recomendaciones en la BD basadas en el análisis automático
        for rec in recomendaciones_automaticas:
            RecomendacionEntrenamiento.objects.create(
                cliente=cliente,
                titulo=rec['titulo'],
                descripcion=rec['descripcion'],
                tipo=rec['tipo'],
                prioridad=rec['prioridad'],
                expires_at=timezone.now() + timedelta(days=30)
            )

        mensaje = f"Se generaron {len(recomendaciones_automaticas)} nuevas recomendaciones."

    context = {
        'cliente': cliente,
        'recomendaciones_activas': recomendaciones_activas,
        'recomendaciones_aplicadas': recomendaciones_aplicadas,
        'recomendaciones_automaticas': recomendaciones_automaticas,
        'mensaje': mensaje,
    }

    return render(request, 'analytics/recomendaciones.html', context)


@login_required
def predicciones(request, cliente_id):
    """
    Sistema de predicciones de rendimiento
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    # Obtener y agrupar ejercicios insensibles a mayúsculas
    todos_ejercicios = calculadora.obtener_ejercicios_tabla()
    ejercicios_dict = {}

    for e in todos_ejercicios:
        clave = e['nombre'].strip().lower()
        if clave not in ejercicios_dict:
            ejercicios_dict[clave] = {
                'nombre_mostrado': e['nombre'].strip().title(),
                'ejercicios': []
            }
        ejercicios_dict[clave]['ejercicios'].append(e)

    ejercicios_unicos = [v['nombre_mostrado'] for v in ejercicios_dict.values()]
    ejercicios_unicos.sort()

    raw_nombre = request.GET.get('ejercicio', None)
    ejercicio_seleccionado = raw_nombre.strip().title() if raw_nombre else (
        ejercicios_unicos[0] if ejercicios_unicos else None)

    predicciones_data = []

    if ejercicio_seleccionado:
        clave = ejercicio_seleccionado.lower()
        ejercicios_filtrados = ejercicios_dict.get(clave, {}).get('ejercicios', [])
        ejercicios_filtrados.sort(key=lambda x: x['fecha'])

        if len(ejercicios_filtrados) >= 3:
            pesos = []
            fechas = []

            for e in ejercicios_filtrados:
                try:
                    peso = float(e.get('peso', 0)) if e.get('peso') != 'PC' else 0
                    if peso > 0:
                        pesos.append(peso)
                        fechas.append(e['fecha'])
                except (ValueError, TypeError):
                    continue

            if len(pesos) >= 3:
                incrementos = [pesos[i] - pesos[i - 1] for i in range(1, len(pesos))]
                incremento_promedio = sum(incrementos) / len(incrementos) if incrementos else 0
                peso_actual = pesos[-1]

                for meses in [1, 3, 6]:
                    peso_predicho = peso_actual + (incremento_promedio * meses * 4)
                    fecha_prediccion = timezone.now().date() + timedelta(days=30 * meses)

                    predicciones_data.append({
                        'ejercicio': ejercicio_seleccionado,
                        'fecha_prediccion': fecha_prediccion.strftime('%Y-%m-%d'),  # ⬅️ aquí el cambio
                        'peso_predicho': max(peso_predicho, peso_actual),
                        'peso_actual': peso_actual,
                        'incremento_esperado': peso_predicho - peso_actual,
                        'meses': meses,
                        'confianza': max(70 - (meses * 10), 30)
                    })

    # Predicciones históricas (no necesitan cambio)
    predicciones_bd = PrediccionRendimiento.objects.filter(
        cliente=cliente,
        activa=True
    ).order_by('-fecha_prediccion')[:10]

    context = {
        'cliente': cliente,
        'ejercicios': ejercicios_unicos,
        'ejercicio_seleccionado': ejercicio_seleccionado,
        'predicciones_data': predicciones_data,
        'predicciones_bd': predicciones_bd,
    }

    return render(request, 'analytics/predicciones.html', context)


# ============================================================================
# APIs PARA DATOS DINÁMICOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_ejercicios_tabla(request, cliente_id):
    """
    API para obtener ejercicios usando la misma lógica que la tabla
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    # Parámetros
    limite = int(request.GET.get('limite', 20))
    ejercicio_filtro = request.GET.get('ejercicio', '')

    ejercicios = calculadora.obtener_ejercicios_tabla()

    # Filtrar por ejercicio si se especifica
    if ejercicio_filtro:
        ejercicios = [e for e in ejercicios if ejercicio_filtro.lower() in e['nombre'].lower()]

    # Limitar resultados
    ejercicios = ejercicios[:limite]

    # Convertir fechas a string para JSON
    for e in ejercicios:
        e['fecha'] = e['fecha'].strftime('%Y-%m-%d')

    return JsonResponse({
        'success': True,
        'ejercicios': ejercicios,
        'total': len(ejercicios)
    })


@login_required
@require_http_methods(["GET"])
def api_metricas_tabla(request, cliente_id):
    """
    API para obtener métricas usando datos de la tabla
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    # Parámetros
    dias = int(request.GET.get('dias', 30))
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=dias)

    metricas = calculadora.calcular_metricas_principales(fecha_inicio, fecha_fin)
    datos_graficos = calculadora.obtener_datos_graficos(fecha_inicio, fecha_fin)

    return JsonResponse({
        'success': True,
        'metricas': metricas,
        'graficos': datos_graficos,
        'periodo': f"{fecha_inicio} - {fecha_fin}"
    })


@login_required
@require_http_methods(["POST"])
def marcar_recomendacion_aplicada(request, recomendacion_id):
    """
    Marcar una recomendación como aplicada
    """
    recomendacion = get_object_or_404(RecomendacionEntrenamiento, id=recomendacion_id)

    recomendacion.aplicada = True
    recomendacion.fecha_aplicacion = timezone.now()
    recomendacion.save()

    return JsonResponse({
        'success': True,
        'message': 'Recomendación marcada como aplicada'
    })


@login_required
@require_http_methods(["GET"])
def api_progresion(request, cliente_id, ejercicio):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    dias = int(request.GET.get('dias', 90))
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=dias)

    datos_progresion = []

    ejercicios = calculadora.obtener_ejercicios_tabla(fecha_inicio, fecha_fin)
    ejercicios_filtrados = [e for e in ejercicios if e['nombre'] == ejercicio]
    ejercicios_filtrados.sort(key=lambda x: x['fecha'])

    for e in ejercicios_filtrados:
        try:
            peso = float(e.get('peso', 0)) if e.get('peso') != 'PC' else 0
            if peso > 0:
                datos_progresion.append({
                    'fecha': e['fecha'].strftime('%Y-%m-%d'),
                    'peso': peso,
                    'series': int(e.get('series', 1)),
                    'repeticiones': int(e.get('repeticiones', 1)),
                    'volumen': peso * int(e.get('series', 1)) * int(e.get('repeticiones', 1))
                })
        except Exception:
            continue

    return JsonResponse({
        'success': True,
        'datos': datos_progresion,
        'ejercicio': ejercicio,
        'periodo': f"{fecha_inicio} - {fecha_fin}"
    })


@login_required
@require_http_methods(["POST"])
def calcular_metricas(request, cliente_id):
    """
    Forzar recálculo de métricas desde la tabla de ejercicios
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)

    try:
        metricas = calculadora.calcular_metricas_principales(fecha_inicio, fecha_fin)
        return JsonResponse({
            'success': True,
            'mensaje': 'Métricas recalculadas correctamente',
            'metricas': metricas
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def generar_recomendaciones(request, cliente_id):
    """
    Genera recomendaciones automáticamente para un cliente usando la calculadora
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)

    # Mapeo claro para prioridad
    PRIORIDADES = {'alta': 1, 'media': 2, 'baja': 3}

    recomendaciones_generadas = []

    progresiones = calculadora.obtener_ejercicios_progresion()
    for prog in progresiones:
        if prog['progresion_peso'] < 5:
            recomendaciones_generadas.append({
                'titulo': f'Estancamiento en {prog["nombre_ejercicio"]}',
                'descripcion': f'El progreso ha sido bajo ({prog["progresion_peso"]:.1f}%)',
                'tipo': 'progresion',
                'prioridad': PRIORIDADES['media']
            })

    for rec in recomendaciones_generadas:
        RecomendacionEntrenamiento.objects.create(
            cliente=cliente,
            titulo=rec['titulo'],
            descripcion=rec['descripcion'],
            tipo=rec['tipo'],
            prioridad=rec['prioridad'],
            expires_at=timezone.now() + timedelta(days=30)
        )

    return JsonResponse({
        'success': True,
        'mensaje': f'{len(recomendaciones_generadas)} recomendaciones creadas.'
    })


from analytics.models import TendenciaProgresion
from datetime import timedelta

from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from urllib.parse import urlencode
import pandas as pd


# (y el resto de tus imports: Cliente, CalculadoraEjerciciosTabla, etc.)

@login_required
def actualizar_tendencias(request, cliente_id):
    """
    Calcula y guarda tendencias para todos los ejercicios del cliente.
    Ahora mantiene el ejercicio seleccionado al redirigir.
    """
    # 2. La vista ahora debe aceptar POST para recibir el campo oculto del formulario
    if request.method != 'POST':
        # Si alguien intenta acceder a esta URL directamente (GET), lo redirigimos
        return redirect('analytics:progresion', cliente_id=cliente_id)

    # Imports locales para mantener la función organizada
    from .progression import ProgressionAnalyzer  # Asumiendo que está en analytics.progression
    from .utils import parse_reps  # Asumiendo que está en analytics.utils

    cliente = get_object_or_404(Cliente, id=cliente_id)
    calculadora = CalculadoraEjerciciosTabla(cliente)
    ejercicios = calculadora.obtener_ejercicios_tabla()

    ejercicios_por_nombre = {}
    for e in ejercicios:
        nombre = e['nombre'].strip().lower()
        if nombre not in ejercicios_por_nombre:
            ejercicios_por_nombre[nombre] = []
        ejercicios_por_nombre[nombre].append(e)

    resultados_guardados = 0
    resumen_tendencias = []

    for nombre_normalizado, lista in ejercicios_por_nombre.items():
        if len(lista) < 3:
            continue

        # ✅ SOLUCIÓN 1: Inicializar las listas ANTES de usarlas en el bucle
        entrenos_validos = []
        datos_validos = []

        for e in lista:
            try:
                peso = float(e['peso']) if e['peso'] != 'PC' else 0
                series, reps = parse_reps(e.get('repeticiones'))

                # Este print ahora no dará error, pero la variable 'nombre' no está definida aquí.
                # Usamos 'nombre_normalizado' que sí existe en este scope.
                print(f"🎯 {nombre_normalizado} → peso: {peso}, reps: {reps}")
                if peso > 0 and reps > 0:
                    rm = round(peso * (1 + reps / 30), 2)
                    entrenos_validos.append({
                        'fecha': e['fecha'],
                        '1rm': rm
                    })
            except Exception as error:
                # Usamos 'nombre_normalizado' para un mensaje de error correcto
                print(f"❌ ERROR en {nombre_normalizado}: {error}")

            if 'peso' in e and e.get('peso') not in [None, 'PC']:
                try:
                    datos_validos.append({
                        'fecha': e['fecha'],
                        'peso': float(e.get('peso'))
                    })
                except (ValueError, TypeError):
                    continue

        if len(datos_validos) < 3:
            continue

        df = pd.DataFrame(datos_validos)
        df = df[df['peso'] > 0]
        if len(df) < 3:
            continue

        df = df.sort_values('fecha')
        nombre_mostrado = lista[0]['nombre'].strip().title()

        try:
            analizador = ProgressionAnalyzer(cliente)
            resultado = analizador.analizar_progresion_ejercicio(nombre_mostrado,
                                                                 periodo_dias=365)  # Usar un período largo

            if resultado and resultado.get('tendencia'):
                tendencia_valor = round(resultado['tendencia'].get('pendiente', 0), 1)
                simbolo = "↗️" if tendencia_valor > 0 else "↘️"
                resumen_tendencias.append(f"{nombre_mostrado} {simbolo} {tendencia_valor}%")

                peso_maximo = df['peso'].max()
                sesiones = len(df)
                fecha_inicio = df['fecha'].min()
                fecha_fin = df['fecha'].max()

                TendenciaProgresion.objects.update_or_create(
                    cliente=cliente,
                    nombre_ejercicio=nombre_mostrado,
                    defaults={
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin,
                        'tendencia_general': tendencia_valor,
                        'peso_maximo': peso_maximo,
                        'sesiones_totales': sesiones
                    }
                )
                resultados_guardados += 1
        except Exception as e:
            print(f"Error al analizar con ProgressionAnalyzer para {nombre_mostrado}: {e}")

    if resultados_guardados > 0:
        texto = ", ".join(resumen_tendencias[:5])
        if len(resumen_tendencias) > 5:
            texto += "..."
        messages.success(request, f"📈 Se guardaron {resultados_guardados} tendencias: {texto}")
    else:
        messages.info(request, "No se detectaron ejercicios con datos suficientes para calcular tendencias.")

    # ✅ SOLUCIÓN 2: Redirección inteligente que mantiene el ejercicio seleccionado
    ejercicio_seleccionado = request.POST.get('ejercicio_actual', None)

    # Construimos la URL base para la redirección
    redirect_url = reverse('analytics:progresion', args=[cliente.id])

    # Si había un ejercicio seleccionado, lo añadimos como parámetro a la URL
    if ejercicio_seleccionado:
        # Usamos urlencode para manejar correctamente los espacios y caracteres especiales
        redirect_url += f'?{urlencode({"ejercicio": ejercicio_seleccionado})}'

    return redirect(redirect_url)


# 📈 DASHBOARD DE PROGRESIÓN AVANZADO - VERSIÓN COMPLETA CORREGIDA
# Todos los métodos implementados para evitar errores

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Avg, Max, Min, Count
from datetime import datetime, timedelta
import json
import numpy as np
from entrenos.utils import parsear_ejercicios
from clientes.models import Cliente
from entrenos.models import EntrenoRealizado


class AnalisisProgresionAvanzado:
    """
    Análisis avanzado de progresión - VERSIÓN COMPLETA
    """

    def __init__(self, cliente):
        self.cliente = cliente
        self.ejercicios_principales = [
            'Press banca', 'Press inclinado', 'Sentadilla', 'Peso muerto',
            'Press militar', 'Dominadas', 'Remo', 'Hip thrust'
        ]

    def calcular_ratios_fuerza(self):
        """
        Calcula ratios de fuerza para balance muscular
        """
        # Obtener 1RM estimados de ejercicios principales
        rms = self._obtener_1rm_ejercicios()

        if not rms:
            return {
                'ratios': [],
                'grafico_radar': {'labels': [], 'valores': [], 'optimos': []},
                'puntos_debiles': []
            }

        ratios = {
            'press_sentadilla': self._calcular_ratio(rms.get('Press banca', 0), rms.get('Sentadilla', 0)),
            'peso_muerto_sentadilla': self._calcular_ratio(rms.get('Peso muerto', 0), rms.get('Sentadilla', 0)),
            'press_militar_banca': self._calcular_ratio(rms.get('Press militar', 0), rms.get('Press banca', 0)),
            'dominadas_remo': self._calcular_ratio(rms.get('Dominadas', 0), rms.get('Remo', 0))
        }

        # Comparar con estándares
        estandares = {
            'press_sentadilla': {'optimo': 0.75, 'rango': (0.65, 0.85)},
            'peso_muerto_sentadilla': {'optimo': 1.25, 'rango': (1.15, 1.35)},
            'press_militar_banca': {'optimo': 0.65, 'rango': (0.55, 0.75)},
            'dominadas_remo': {'optimo': 1.0, 'rango': (0.85, 1.15)}
        }

        analisis_ratios = []
        for ratio_name, valor in ratios.items():
            if valor > 0:
                estandar = estandares[ratio_name]
                estado = self._evaluar_ratio(valor, estandar)
                analisis_ratios.append({
                    'nombre': ratio_name.replace('_', ' ').title(),
                    'valor': valor,
                    'optimo': estandar['optimo'],
                    'estado': estado,
                    'recomendacion': self._generar_recomendacion_ratio(ratio_name, estado)
                })

        return {
            'ratios': analisis_ratios,
            'grafico_radar': self._generar_datos_radar(ratios, estandares),
            'puntos_debiles': self._identificar_puntos_debiles(analisis_ratios)
        }

    def analisis_evolucion_temporal(self, ejercicio=None, periodo_dias=90):
        """
        Análisis de evolución temporal con gráficos de línea
        """
        fecha_inicio = datetime.now().date() - timedelta(days=periodo_dias)

        if ejercicio:
            ejercicios = [ejercicio]
        else:
            ejercicios = self.ejercicios_principales

        datos_evolucion = {}

        for ej in ejercicios:
            datos_ejercicio = self._obtener_datos_temporales(ej, fecha_inicio)
            if datos_ejercicio:
                # Calcular tendencias
                try:
                    from scipy import stats
                    tendencia = self._calcular_tendencia_lineal(datos_ejercicio)
                except ImportError:
                    tendencia = self._calcular_tendencia_simple(datos_ejercicio)

                # Detectar hitos y objetivos
                hitos = self._detectar_hitos(datos_ejercicio)

                # Predicciones basadas en progresión actual
                predicciones = self._generar_predicciones_temporales(datos_ejercicio, tendencia)

                datos_evolucion[ej] = {
                    'datos': datos_ejercicio,
                    'tendencia': tendencia,
                    'hitos': hitos,
                    'predicciones': predicciones,
                    'volumen_por_grupo': self._calcular_volumen_grupo_muscular(ej, fecha_inicio)
                }

        return datos_evolucion

    def analisis_mesociclos(self, periodo_dias=180):
        """
        Análisis de mesociclos para periodización
        """
        fecha_inicio = datetime.now().date() - timedelta(days=periodo_dias)

        # Dividir en mesociclos de 4 semanas
        mesociclos = self._dividir_en_mesociclos(fecha_inicio, 28)

        analisis_mesociclos = []

        for i, (inicio, fin) in enumerate(mesociclos):
            datos_mesociclo = self._analizar_mesociclo(inicio, fin)

            # Comparar con mesociclo anterior
            if i > 0:
                mesociclo_anterior = analisis_mesociclos[i - 1]
                comparativa = self._comparar_mesociclos(datos_mesociclo, mesociclo_anterior['datos'])
                datos_mesociclo['comparativa'] = comparativa

            analisis_mesociclos.append({
                'numero': i + 1,
                'fecha_inicio': inicio,
                'fecha_fin': fin,
                'datos': datos_mesociclo,
                'efectividad': self._evaluar_efectividad_mesociclo(datos_mesociclo),
                'recomendaciones': self._generar_recomendaciones_mesociclo(datos_mesociclo)
            })

        return {
            'mesociclos': analisis_mesociclos,
            'periodizacion_optima': self._sugerir_periodizacion_optima(analisis_mesociclos),
            'picos_valles': self._identificar_picos_valles_rendimiento(analisis_mesociclos)
        }

    # ============================================================================
    # MÉTODOS AUXILIARES IMPLEMENTADOS
    # ============================================================================

    def _obtener_1rm_ejercicios(self):
        """
        Calcula 1RM estimado usando fórmula de Brzycki
        """
        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=datetime.now().date() - timedelta(days=30)
        ).exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

        rms = {}

        for entreno in entrenamientos:
            ejercicios = parsear_ejercicios(entreno.notas_liftin)

            for ejercicio in ejercicios:
                nombre = ejercicio['nombre']
                if nombre in self.ejercicios_principales:
                    try:
                        peso = float(ejercicio.get('peso', 0)) if ejercicio.get('peso') != 'PC' else 0
                        reps = self._extraer_repeticiones(ejercicio.get('repeticiones', '1'))

                        if peso > 0 and reps > 0 and reps <= 12:
                            # Fórmula de Brzycki: 1RM = peso / (1.0278 - 0.0278 * reps)
                            rm_estimado = peso / (1.0278 - 0.0278 * reps)

                            if nombre not in rms or rm_estimado > rms[nombre]:
                                rms[nombre] = round(rm_estimado, 1)

                    except (ValueError, TypeError):
                        continue

        return rms

    def _calcular_ratio(self, valor1, valor2):
        """
        Calcula ratio entre dos valores
        """
        if valor2 > 0:
            return round(valor1 / valor2, 2)
        return 0

    def _evaluar_ratio(self, valor, estandar):
        """
        Evalúa si un ratio está en rango óptimo
        """
        rango_min, rango_max = estandar['rango']

        if rango_min <= valor <= rango_max:
            return 'optimo'
        elif valor < rango_min:
            return 'bajo'
        else:
            return 'alto'

    def _generar_recomendacion_ratio(self, ratio_name, estado):
        """
        Genera recomendaciones basadas en ratios
        """
        recomendaciones = {
            'press_sentadilla': {
                'bajo': 'Enfócate en fortalecer el press de banca. Agrega más volumen de empuje horizontal.',
                'alto': 'Prioriza el entrenamiento de piernas. Aumenta frecuencia de sentadillas.',
                'optimo': 'Mantén el equilibrio actual entre empuje y piernas.'
            },
            'peso_muerto_sentadilla': {
                'bajo': 'Trabaja más el peso muerto y cadena posterior. Agrega RDL y hip thrust.',
                'alto': 'Equilibra con más trabajo de cuádriceps. Aumenta volumen de sentadillas.',
                'optimo': 'Excelente equilibrio entre cadena anterior y posterior.'
            },
            'press_militar_banca': {
                'bajo': 'Incrementa el trabajo de hombros. Agrega press militar y elevaciones.',
                'alto': 'Reduce volumen de press militar, mantén press banca.',
                'optimo': 'Buen equilibrio entre empuje horizontal y vertical.'
            },
            'dominadas_remo': {
                'bajo': 'Aumenta trabajo de dominadas y tracción vertical.',
                'alto': 'Equilibra con más remo horizontal.',
                'optimo': 'Excelente equilibrio en el trabajo de espalda.'
            }
        }

        return recomendaciones.get(ratio_name, {}).get(estado, 'Mantén el entrenamiento actual.')

    def _generar_datos_radar(self, ratios, estandares):
        """
        Genera datos para el gráfico radar
        """
        labels = []
        valores = []
        optimos = []

        for ratio_name, valor in ratios.items():
            if valor > 0:
                labels.append(ratio_name.replace('_', ' ').title())
                valores.append(valor)
                optimos.append(estandares[ratio_name]['optimo'])

        return {
            'labels': labels,
            'valores': valores,
            'optimos': optimos
        }

    def _identificar_puntos_debiles(self, analisis_ratios):
        """
        Identifica puntos débiles basados en ratios
        """
        puntos_debiles = []

        for ratio in analisis_ratios:
            if ratio['estado'] != 'optimo':
                puntos_debiles.append(f"{ratio['nombre']}: {ratio['recomendacion']}")

        return puntos_debiles

    def _obtener_datos_temporales(self, ejercicio, fecha_inicio):
        """
        Obtiene datos temporales de un ejercicio específico
        """
        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio
        ).exclude(notas_liftin__isnull=True).exclude(notas_liftin='').order_by('fecha')

        datos = []

        for entreno in entrenamientos:
            ejercicios = parsear_ejercicios(entreno.notas_liftin)

            for ej in ejercicios:
                if ej['nombre'] == ejercicio:
                    try:
                        peso = float(ej.get('peso', 0)) if ej.get('peso') != 'PC' else 0
                        reps = self._extraer_repeticiones(ej.get('repeticiones', '1'))
                        series = self._extraer_series(ej.get('repeticiones', '1'))

                        if peso > 0:
                            volumen = peso * series * reps
                            intensidad = (peso / self._obtener_1rm_estimado(ejercicio, peso,
                                                                            reps)) * 100 if reps <= 12 else 70

                            datos.append({
                                'fecha': entreno.fecha.strftime('%Y-%m-%d'),
                                'peso': peso,
                                'repeticiones': reps,
                                'series': series,
                                'volumen': volumen,
                                'intensidad': round(intensidad, 1)
                            })

                    except (ValueError, TypeError):
                        continue

        return datos

    def _calcular_tendencia_lineal(self, datos):
        """
        Calcula tendencia lineal usando regresión
        """
        if len(datos) < 3:
            return None

        try:
            from scipy import stats
            # Convertir fechas a números para regresión
            fechas_num = [
                (datetime.strptime(d['fecha'], '%Y-%m-%d') - datetime.strptime(datos[0]['fecha'], '%Y-%m-%d')).days for
                d in datos]
            pesos = [d['peso'] for d in datos]

            # Regresión lineal
            slope, intercept, r_value, p_value, std_err = stats.linregress(fechas_num, pesos)

            return {
                'pendiente': round(slope, 3),
                'intercepto': round(intercept, 2),
                'correlacion': round(r_value, 3),
                'p_value': round(p_value, 3),
                'tendencia_semanal': round(slope * 7, 2),
                'confianza': round(abs(r_value) * 100, 1)
            }
        except ImportError:
            return self._calcular_tendencia_simple(datos)

    def _calcular_tendencia_simple(self, datos):
        """
        Calcula tendencia simple sin scipy
        """
        if len(datos) < 3:
            return None

        primer_peso = datos[0]['peso']
        ultimo_peso = datos[-1]['peso']

        if primer_peso > 0:
            cambio_porcentual = ((ultimo_peso - primer_peso) / primer_peso) * 100
            dias_transcurridos = (datetime.strptime(datos[-1]['fecha'], '%Y-%m-%d') -
                                  datetime.strptime(datos[0]['fecha'], '%Y-%m-%d')).days

            tendencia_semanal = (cambio_porcentual / dias_transcurridos) * 7 if dias_transcurridos > 0 else 0

            return {
                'pendiente': round((ultimo_peso - primer_peso) / len(datos), 3),
                'intercepto': primer_peso,
                'correlacion': 0.8,  # Valor estimado
                'p_value': 0.05,
                'tendencia_semanal': round(tendencia_semanal, 2),
                'confianza': 75.0
            }

        return None

    def _detectar_hitos(self, datos):
        """
        Detecta hitos importantes en la progresión
        """
        if not datos:
            return []

        hitos = []
        pesos = [d['peso'] for d in datos]

        # Peso máximo
        peso_max = max(pesos)
        fecha_max = next(d['fecha'] for d in datos if d['peso'] == peso_max)
        hitos.append({
            'tipo': 'record_personal',
            'fecha': fecha_max,
            'valor': peso_max,
            'descripcion': f'Nuevo récord personal: {peso_max} kg'
        })

        # Incrementos significativos (>5%)
        for i in range(1, len(datos)):
            if datos[i - 1]['peso'] > 0:
                incremento = ((datos[i]['peso'] - datos[i - 1]['peso']) / datos[i - 1]['peso']) * 100
                if incremento >= 5:
                    hitos.append({
                        'tipo': 'incremento_significativo',
                        'fecha': datos[i]['fecha'],
                        'valor': datos[i]['peso'],
                        'descripcion': f'Incremento del {incremento:.1f}%'
                    })

        return hitos

    def _generar_predicciones_temporales(self, datos, tendencia):
        """
        Genera predicciones basadas en progresión actual
        """
        if not tendencia or len(datos) < 3:
            return []

        ultimo_dato = datos[-1]
        fecha_base = datetime.strptime(ultimo_dato['fecha'], '%Y-%m-%d')

        predicciones = []

        # Predicciones a 4, 8 y 12 semanas
        for semanas in [4, 8, 12]:
            fecha_prediccion = fecha_base + timedelta(weeks=semanas)
            peso_predicho = ultimo_dato['peso'] + (tendencia['tendencia_semanal'] * semanas)

            # Ajustar confianza según tiempo
            confianza = max(tendencia['confianza'] - (semanas * 5), 30)

            predicciones.append({
                'fecha': fecha_prediccion.strftime('%Y-%m-%d'),
                'peso_estimado': round(peso_predicho, 1),
                'confianza': round(confianza, 1),
                'semanas': semanas
            })

        return predicciones

    def _calcular_volumen_grupo_muscular(self, ejercicio, fecha_inicio):
        """
        Calcula volumen total por grupo muscular
        """
        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio
        ).exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

        volumen_total = 0

        for entreno in entrenamientos:
            ejercicios = parsear_ejercicios(entreno.notas_liftin)

            for ej in ejercicios:
                if ej['nombre'] == ejercicio:
                    try:
                        peso = float(ej.get('peso', 0)) if ej.get('peso') != 'PC' else 0
                        reps = self._extraer_repeticiones(ej.get('repeticiones', '1'))
                        series = self._extraer_series(ej.get('repeticiones', '1'))

                        volumen_total += peso * series * reps
                    except (ValueError, TypeError):
                        continue

        return volumen_total

    def _dividir_en_mesociclos(self, fecha_inicio, dias_por_ciclo):
        """
        Divide el período en mesociclos
        """
        mesociclos = []
        fecha_actual = fecha_inicio
        fecha_fin_total = datetime.now().date()

        while fecha_actual < fecha_fin_total:
            fecha_fin_ciclo = fecha_actual + timedelta(days=dias_por_ciclo)
            if fecha_fin_ciclo > fecha_fin_total:
                fecha_fin_ciclo = fecha_fin_total

            mesociclos.append((fecha_actual, fecha_fin_ciclo))
            fecha_actual = fecha_fin_ciclo + timedelta(days=1)

        return mesociclos

    def _analizar_mesociclo(self, fecha_inicio, fecha_fin):
        """
        Analiza un mesociclo específico
        """
        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )

        carga_total = 0
        duracion_total = 0
        sesiones = entrenamientos.count()

        for entreno in entrenamientos:
            duracion_total += entreno.duracion_minutos or 0

            if entreno.notas_liftin:
                ejercicios = parsear_ejercicios(entreno.notas_liftin)
                for ej in ejercicios:
                    try:
                        peso = float(ej.get('peso', 0)) if ej.get('peso') != 'PC' else 0
                        reps = self._extraer_repeticiones(ej.get('repeticiones', '1'))
                        series = self._extraer_series(ej.get('repeticiones', '1'))
                        carga_total += peso * series * reps
                    except (ValueError, TypeError):
                        continue

        return {
            'carga_total': carga_total,
            'duracion_total': duracion_total,
            'sesiones': sesiones,
            'carga_promedio': carga_total / sesiones if sesiones > 0 else 0,
            'duracion_promedio': duracion_total / sesiones if sesiones > 0 else 0
        }

    def _comparar_mesociclos(self, mesociclo_actual, mesociclo_anterior):
        """
        Compara dos mesociclos
        """
        if not mesociclo_anterior:
            return None

        cambio_carga = mesociclo_actual['carga_total'] - mesociclo_anterior['carga_total']
        cambio_sesiones = mesociclo_actual['sesiones'] - mesociclo_anterior['sesiones']

        return {
            'cambio_carga': cambio_carga,
            'cambio_carga_pct': (cambio_carga / mesociclo_anterior['carga_total']) * 100 if mesociclo_anterior[
                                                                                                'carga_total'] > 0 else 0,
            'cambio_sesiones': cambio_sesiones,
            'mejora': cambio_carga > 0
        }

    def _evaluar_efectividad_mesociclo(self, datos_mesociclo):
        """
        Evalúa la efectividad de un mesociclo
        """
        if datos_mesociclo['sesiones'] >= 12 and datos_mesociclo['carga_promedio'] > 1000:
            return 'alta'
        elif datos_mesociclo['sesiones'] >= 8 and datos_mesociclo['carga_promedio'] > 500:
            return 'media'
        else:
            return 'baja'

    def _generar_recomendaciones_mesociclo(self, datos_mesociclo):
        """
        Genera recomendaciones para el mesociclo
        """
        recomendaciones = []

        if datos_mesociclo['sesiones'] < 8:
            recomendaciones.append('Aumentar frecuencia de entrenamiento')

        if datos_mesociclo['carga_promedio'] < 500:
            recomendaciones.append('Incrementar intensidad o volumen')

        if datos_mesociclo['duracion_promedio'] > 90:
            recomendaciones.append('Considerar reducir duración de sesiones')

        if not recomendaciones:
            recomendaciones.append('Mantener el enfoque actual')

        return recomendaciones

    def _sugerir_periodizacion_optima(self, analisis_mesociclos):
        """
        Sugiere periodización óptima
        """
        if not analisis_mesociclos:
            return "Datos insuficientes para sugerir periodización"

        efectividades = [m['efectividad'] for m in analisis_mesociclos]

        if efectividades.count('alta') > len(efectividades) / 2:
            return "Continúa con la periodización actual, está funcionando bien"
        else:
            return "Considera alternar mesociclos de alta y baja intensidad para mejor recuperación"

    def _identificar_picos_valles_rendimiento(self, analisis_mesociclos):
        """
        Identifica picos y valles de rendimiento
        """
        if len(analisis_mesociclos) < 3:
            return []

        picos_valles = []

        for i in range(1, len(analisis_mesociclos) - 1):
            actual = analisis_mesociclos[i]['datos']['carga_total']
            anterior = analisis_mesociclos[i - 1]['datos']['carga_total']
            siguiente = analisis_mesociclos[i + 1]['datos']['carga_total']

            if actual > anterior and actual > siguiente:
                picos_valles.append({
                    'tipo': 'pico',
                    'mesociclo': analisis_mesociclos[i]['numero'],
                    'valor': actual
                })
            elif actual < anterior and actual < siguiente:
                picos_valles.append({
                    'tipo': 'valle',
                    'mesociclo': analisis_mesociclos[i]['numero'],
                    'valor': actual
                })

        return picos_valles

    def _extraer_repeticiones(self, rep_str):
        """
        Extrae número de repeticiones de string como "3x8"
        """
        try:
            rep_str = str(rep_str).lower().replace('×', 'x').replace(' ', '')
            if 'x' in rep_str:
                return int(rep_str.split('x')[1])
            return int(rep_str)
        except:
            return 1

    def _extraer_series(self, rep_str):
        """
        Extrae número de series de string como "3x8"
        """
        try:
            rep_str = str(rep_str).lower().replace('×', 'x').replace(' ', '')
            if 'x' in rep_str:
                return int(rep_str.split('x')[0])
            return 1
        except:
            return 1

    def _obtener_1rm_estimado(self, ejercicio, peso, reps):
        """
        Obtiene 1RM estimado para un ejercicio
        """
        if reps <= 12:
            return peso / (1.0278 - 0.0278 * reps)
        return peso * 1.3  # Estimación conservadora para altas repeticiones


# Vista para el Dashboard de Progresión Avanzado
def dashboard_progresion_avanzado(request, cliente_id):
    """
    Vista principal del Dashboard de Progresión Avanzado
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    analizador = AnalisisProgresionAvanzado(cliente)

    # Obtener parámetros
    ejercicio_seleccionado = request.GET.get('ejercicio')
    periodo = int(request.GET.get('periodo', 90))

    # Análisis de ratios de fuerza
    ratios_fuerza = analizador.calcular_ratios_fuerza()

    # Evolución temporal
    evolucion_temporal = analizador.analisis_evolucion_temporal(ejercicio_seleccionado, periodo)

    # Análisis de mesociclos
    analisis_mesociclos = analizador.analisis_mesociclos()

    # Lista de ejercicios disponibles
    ejercicios_disponibles = list(evolucion_temporal.keys()) if evolucion_temporal else []

    context = {
        'cliente': cliente,
        'ejercicio_seleccionado': ejercicio_seleccionado,
        'periodo': periodo,
        'ejercicios_disponibles': ejercicios_disponibles,
        'ratios_fuerza': ratios_fuerza,
        'evolucion_temporal': evolucion_temporal,
        'analisis_mesociclos': analisis_mesociclos,
        'datos_graficos': json.dumps({
            'evolucion': evolucion_temporal,
            'ratios': ratios_fuerza
        })
    }

    return render(request, 'analytics/progresion_avanzado.html', context)


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Avg, Max, Min, Count
from datetime import datetime, timedelta
import json
import numpy as np
from entrenos.utils import parsear_ejercicios
from clientes.models import Cliente
from entrenos.models import EntrenoRealizado


class AnalisisIntensidadAvanzado:
    """
    Análisis avanzado de intensidad - VERSIÓN COMPLETA
    """

    def __init__(self, cliente):
        self.cliente = cliente
        self.zonas_fc = {
            'recuperacion': {'min': 50, 'max': 60},
            'aerobica': {'min': 60, 'max': 70},
            'umbral': {'min': 70, 'max': 80},
            'anaerobica': {'min': 80, 'max': 90}
        }

    def analizar_zonas_entrenamiento(self, periodo_dias=30):
        """
        Analiza distribución de zonas de entrenamiento
        """
        fecha_inicio = datetime.now().date() - timedelta(days=periodo_dias)

        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio
        )

        distribucion = {
            'recuperacion': {'tiempo': 0, 'porcentaje': 0, 'calorias': 0},
            'aerobica': {'tiempo': 0, 'porcentaje': 0, 'calorias': 0},
            'umbral': {'tiempo': 0, 'porcentaje': 0, 'calorias': 0},
            'anaerobica': {'tiempo': 0, 'porcentaje': 0, 'calorias': 0}
        }

        tiempo_total = 0

        for entreno in entrenamientos:
            duracion = entreno.duracion_minutos or 60  # Default 60 min
            tiempo_total += duracion

            # Estimar zona basada en tipo de entrenamiento
            zona = self._estimar_zona_entrenamiento(entreno)

            distribucion[zona]['tiempo'] += duracion
            distribucion[zona]['calorias'] += self._calcular_calorias_zona(zona, duracion)

        # Calcular porcentajes
        if tiempo_total > 0:
            for zona in distribucion:
                distribucion[zona]['porcentaje'] = round(
                    (distribucion[zona]['tiempo'] / tiempo_total) * 100, 1
                )

        # Generar recomendaciones
        recomendaciones = self._generar_recomendaciones_zonas(distribucion)

        return {
            'distribucion': distribucion,
            'tiempo_total': tiempo_total,
            'recomendaciones_zonas': recomendaciones
        }

    def analizar_carga_entrenamiento(self, periodo_dias=90):
        """
        Analiza carga de entrenamiento semanal/mensual
        """
        fecha_inicio = datetime.now().date() - timedelta(days=periodo_dias)

        # Obtener datos por semana
        carga_semanal = {}
        semana_actual = fecha_inicio

        while semana_actual <= datetime.now().date():
            fin_semana = semana_actual + timedelta(days=6)

            entrenamientos_semana = EntrenoRealizado.objects.filter(
                cliente=self.cliente,
                fecha__gte=semana_actual,
                fecha__lte=fin_semana
            )

            carga_total = 0
            sesiones = entrenamientos_semana.count()
            duracion_total = 0

            for entreno in entrenamientos_semana:
                duracion = entreno.duracion_minutos or 60
                duracion_total += duracion

                # Calcular carga basada en volumen y duración
                if entreno.notas_liftin:
                    ejercicios = parsear_ejercicios(entreno.notas_liftin)
                    volumen_entreno = self._calcular_volumen_entreno(ejercicios)
                    intensidad_estimada = self._estimar_intensidad_entreno(ejercicios)

                    # Fórmula de carga: Volumen × Intensidad × Factor tiempo
                    carga_entreno = (volumen_entreno * intensidad_estimada * duracion) / 1000
                    carga_total += carga_entreno

            semana_str = semana_actual.strftime('%Y-W%U')
            carga_semanal[semana_str] = {
                'carga_total': round(carga_total, 1),
                'sesiones': sesiones,
                'duracion_total': duracion_total,
                'carga_promedio': round(carga_total / sesiones, 1) if sesiones > 0 else 0
            }

            semana_actual += timedelta(days=7)

        # Calcular tendencias
        cargas = [data['carga_total'] for data in carga_semanal.values()]
        tendencia = self._calcular_tendencia_carga(cargas)

        # Estadísticas generales
        carga_promedio = sum(cargas) / len(cargas) if cargas else 0
        sesiones_promedio = sum(data['sesiones'] for data in carga_semanal.values()) / len(
            carga_semanal) if carga_semanal else 0
        duracion_promedio = sum(data['duracion_total'] for data in carga_semanal.values()) / len(
            carga_semanal) if carga_semanal else 0

        # Recomendaciones de carga
        recomendaciones = self._generar_recomendaciones_carga(carga_promedio, tendencia)

        return {
            'carga_semanal': carga_semanal,
            'carga_promedio': round(carga_promedio, 1),
            'sesiones_promedio': round(sesiones_promedio, 1),
            'duracion_promedio': round(duracion_promedio, 1),
            'tendencia': tendencia,
            'recomendaciones_carga': recomendaciones
        }

    def analizar_distribucion_intensidades(self, periodo_dias=60):
        """
        Analiza distribución de intensidades por % 1RM
        """
        fecha_inicio = datetime.now().date() - timedelta(days=periodo_dias)

        entrenamientos = EntrenoRealizado.objects.filter(
            cliente=self.cliente,
            fecha__gte=fecha_inicio
        ).exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

        distribucion = {
            'recuperacion': 0,  # 40-60% 1RM
            'hipertrofia': 0,  # 60-80% 1RM
            'fuerza': 0,  # 80-90% 1RM
            'potencia': 0  # 90-100% 1RM
        }

        total_series = 0

        for entreno in entrenamientos:
            ejercicios = parsear_ejercicios(entreno.notas_liftin)

            for ejercicio in ejercicios:
                try:
                    peso = float(ejercicio.get('peso', 0)) if ejercicio.get('peso') != 'PC' else 0
                    reps = self._extraer_repeticiones(ejercicio.get('repeticiones', '1'))
                    series = self._extraer_series(ejercicio.get('repeticiones', '1'))

                    if peso > 0 and reps > 0:
                        # Estimar 1RM
                        rm_estimado = self._calcular_1rm(peso, reps)
                        intensidad_pct = (peso / rm_estimado) * 100 if rm_estimado > 0 else 50

                        # Clasificar por zona de intensidad
                        zona = self._clasificar_intensidad(intensidad_pct)
                        distribucion[zona] += series
                        total_series += series

                except (ValueError, TypeError):
                    continue

        # Convertir a porcentajes
        if total_series > 0:
            for zona in distribucion:
                distribucion[zona] = round((distribucion[zona] / total_series) * 100, 1)

        # Evaluar efectividad de rutina
        efectividad = self._evaluar_efectividad_rutina(distribucion)

        # Recomendaciones de intensidad
        recomendaciones = self._generar_recomendaciones_intensidad(distribucion)

        return {
            'distribucion': distribucion,
            'total_series': total_series,
            'efectividad_rutina': efectividad,
            'recomendaciones_intensidad': recomendaciones
        }

    # Dentro de la clase AnalisisIntensidadAvanzado
    # Dentro de la clase AnalisisIntensidadAvanzado
    # Dentro de la clase AnalisisIntensidadAvanzado
    from django.utils import timezone  # <-- ¡ASEGÚRATE DE TENER ESTA IMPORTACIÓN!

    def calcular_fatiga_acumulada(self, periodo_dias=14):
        """
        Calcula fatiga acumulada - VERSIÓN FINAL CON MANEJO DE ZONA HORARIA.
        """
        logger.info("--- INICIANDO CÁLCULO DE FATIGA (VERSIÓN TIMEZONE) ---")

        # Usamos timezone.now() para obtener la fecha actual de forma segura en Django
        hoy = timezone.now().date()

        ultimo_entreno = EntrenoRealizado.objects.filter(cliente=self.cliente).order_by('-fecha').first()

        if not ultimo_entreno:
            logger.info("No se encontraron entrenamientos. Fatiga es 0.")
            return {'fatiga_actual': 0, 'nivel': 'baja', 'recomendacion_descanso': "Estás completamente recuperado.",
                    'dias_recuperacion': 0}

        logger.info(f"Último entreno encontrado en fecha: {ultimo_entreno.fecha}")

        # Asumimos que la fatiga justo después del último entreno es la carga de ese día.
        carga_ultimo_entreno = self._calcular_carga_dia(ultimo_entreno)
        logger.info(f"Carga calculada para el último entreno: {carga_ultimo_entreno}")

        fatiga_post_entreno = carga_ultimo_entreno

        # --- Aplicar decaimiento desde el último entreno hasta HOY ---
        dias_de_recuperacion = (hoy - ultimo_entreno.fecha).days

        logger.info(f"Fecha de hoy (consciente de timezone): {hoy}. Días de recuperación: {dias_de_recuperacion}")

        if dias_de_recuperacion < 0:
            logger.warning("La fecha del último entreno es en el futuro. Se tratará como 0 días de recuperación.")
            dias_de_recuperacion = 0

        decay_factor = 0.85
        fatiga_actual = fatiga_post_entreno * (decay_factor ** dias_de_recuperacion)

        logger.info(
            f"Cálculo final: {fatiga_post_entreno:.2f} * ({decay_factor} ** {dias_de_recuperacion}) = {fatiga_actual:.2f}")

        # El resto de la lógica...
        nivel_fatiga = self._evaluar_nivel_fatiga(fatiga_actual)
        dias_rec_recomendados = self._calcular_dias_recuperacion(fatiga_actual)
        recomendacion = self._generar_recomendacion_descanso(nivel_fatiga, dias_rec_recomendados)

        resultado = {
            'fatiga_actual': round(fatiga_actual, 1),
            'nivel': nivel_fatiga,
            'dias_recuperacion': dias_rec_recomendados,
            'recomendacion_descanso': recomendacion
        }
        logger.info(f"--- CÁLCULO DE FATIGA FINALIZADO: {resultado} ---")
        return resultado

    # ============================================================================
    # MÉTODOS AUXILIARES IMPLEMENTADOS
    # ============================================================================

    def _estimar_zona_entrenamiento(self, entreno):
        """
        Estima zona de entrenamiento basada en características del entreno
        """
        duracion = entreno.duracion_minutos or 60

        if entreno.notas_liftin:
            ejercicios = parsear_ejercicios(entreno.notas_liftin)
            intensidad_promedio = self._calcular_intensidad_promedio(ejercicios)

            if intensidad_promedio >= 85:
                return 'anaerobica'
            elif intensidad_promedio >= 75:
                return 'umbral'
            elif intensidad_promedio >= 65:
                return 'aerobica'
            else:
                return 'recuperacion'

        # Estimación basada en duración si no hay datos
        if duracion <= 30:
            return 'anaerobica'
        elif duracion <= 60:
            return 'umbral'
        elif duracion <= 90:
            return 'aerobica'
        else:
            return 'recuperacion'

    def _calcular_calorias_zona(self, zona, duracion_minutos):
        """
        Calcula calorías quemadas por zona
        """
        calorias_por_minuto = {
            'recuperacion': 4,  # 4 cal/min
            'aerobica': 5,  # 5 cal/min
            'umbral': 6,  # 6 cal/min
            'anaerobica': 8  # 8 cal/min
        }

        return duracion_minutos * calorias_por_minuto.get(zona, 5)

    def _generar_recomendaciones_zonas(self, distribucion):
        """
        Genera recomendaciones basadas en distribución de zonas
        """
        recomendaciones = []

        # Verificar distribución óptima
        if distribucion['recuperacion']['porcentaje'] < 10:
            recomendaciones.append('Aumenta el tiempo en zona de recuperación para mejor adaptación')

        if distribucion['aerobica']['porcentaje'] < 30:
            recomendaciones.append('Incrementa el trabajo aeróbico para mejorar la base cardiovascular')

        if distribucion['anaerobica']['porcentaje'] > 25:
            recomendaciones.append('Reduce el tiempo en zona anaeróbica para evitar sobreentrenamiento')

        if not recomendaciones:
            recomendaciones.append('Distribución de zonas óptima, mantén el enfoque actual')

        return recomendaciones

    def _calcular_volumen_entreno(self, ejercicios):
        """
        Calcula volumen total de un entrenamiento
        """
        volumen_total = 0

        for ejercicio in ejercicios:
            try:
                peso = float(ejercicio.get('peso', 0)) if ejercicio.get('peso') != 'PC' else 0
                reps = self._extraer_repeticiones(ejercicio.get('repeticiones', '1'))
                series = self._extraer_series(ejercicio.get('repeticiones', '1'))

                volumen_total += peso * series * reps
            except (ValueError, TypeError):
                continue

        return volumen_total

    def _estimar_intensidad_entreno(self, ejercicios):
        """
        Estima intensidad promedio de un entrenamiento
        """
        intensidades = []

        for ejercicio in ejercicios:
            try:
                peso = float(ejercicio.get('peso', 0)) if ejercicio.get('peso') != 'PC' else 0
                reps = self._extraer_repeticiones(ejercicio.get('repeticiones', '1'))

                if peso > 0 and reps > 0:
                    # Estimar intensidad basada en repeticiones
                    if reps <= 3:
                        intensidad = 90  # Fuerza máxima
                    elif reps <= 6:
                        intensidad = 85  # Fuerza
                    elif reps <= 12:
                        intensidad = 75  # Hipertrofia
                    else:
                        intensidad = 60  # Resistencia

                    intensidades.append(intensidad)
            except (ValueError, TypeError):
                continue

        return sum(intensidades) / len(intensidades) if intensidades else 70

    def _calcular_tendencia_carga(self, cargas):
        """
        Calcula tendencia de carga
        """
        if len(cargas) < 2:
            return {'direccion': 'estable', 'porcentaje': 0}

        primera_mitad = cargas[:len(cargas) // 2]
        segunda_mitad = cargas[len(cargas) // 2:]

        promedio_inicial = sum(primera_mitad) / len(primera_mitad)
        promedio_final = sum(segunda_mitad) / len(segunda_mitad)

        if promedio_inicial > 0:
            cambio_porcentual = ((promedio_final - promedio_inicial) / promedio_inicial) * 100

            if cambio_porcentual > 5:
                direccion = 'subiendo'
            elif cambio_porcentual < -5:
                direccion = 'bajando'
            else:
                direccion = 'estable'

            return {
                'direccion': direccion,
                'porcentaje': round(abs(cambio_porcentual), 1)
            }

        return {'direccion': 'estable', 'porcentaje': 0}

    def _generar_recomendaciones_carga(self, carga_promedio, tendencia):
        """
        Genera recomendaciones de carga
        """
        recomendaciones = []

        if carga_promedio < 300:
            recomendaciones.append('Carga muy baja. Considera aumentar volumen o intensidad')
        elif carga_promedio > 1000:
            recomendaciones.append('Carga muy alta. Monitorea signos de sobreentrenamiento')

        if tendencia['direccion'] == 'subiendo' and tendencia['porcentaje'] > 20:
            recomendaciones.append('Incremento de carga muy rápido. Considera progresión más gradual')
        elif tendencia['direccion'] == 'bajando' and tendencia['porcentaje'] > 15:
            recomendaciones.append('Reducción significativa de carga. Evalúa si es intencional')

        if not recomendaciones:
            recomendaciones.append('Carga de entrenamiento en rango óptimo')

        return recomendaciones

    def _calcular_1rm(self, peso, reps):
        """
        Calcula 1RM usando fórmula de Brzycki
        """
        if reps <= 12:
            return peso / (1.0278 - 0.0278 * reps)
        return peso * 1.3  # Estimación para altas repeticiones

    def _clasificar_intensidad(self, intensidad_pct):
        """
        Clasifica intensidad por % 1RM
        """
        if intensidad_pct >= 90:
            return 'potencia'
        elif intensidad_pct >= 80:
            return 'fuerza'
        elif intensidad_pct >= 60:
            return 'hipertrofia'
        else:
            return 'recuperacion'

    def _evaluar_efectividad_rutina(self, distribucion):
        """
        Evalúa efectividad de la rutina basada en distribución
        """
        # Distribución óptima para hipertrofia/fuerza general
        if (distribucion['hipertrofia'] >= 50 and
                distribucion['fuerza'] >= 20 and
                distribucion['recuperacion'] >= 10):
            return 'Rutina muy efectiva para hipertrofia y fuerza'
        elif distribucion['hipertrofia'] >= 40:
            return 'Rutina efectiva, considera agregar más trabajo de fuerza'
        else:
            return 'Rutina necesita ajustes en distribución de intensidades'

    def _generar_recomendaciones_intensidad(self, distribucion):
        """
        Genera recomendaciones de intensidad
        """
        recomendaciones = []

        if distribucion['hipertrofia'] < 40:
            recomendaciones.append('Aumenta el trabajo en rango de hipertrofia (60-80% 1RM)')

        if distribucion['fuerza'] < 15:
            recomendaciones.append('Incluye más trabajo de fuerza (80-90% 1RM)')

        if distribucion['recuperacion'] < 5:
            recomendaciones.append('Agrega series de recuperación activa (40-60% 1RM)')

        if distribucion['potencia'] > 10:
            recomendaciones.append('Reduce el trabajo de potencia para evitar fatiga excesiva')

        if not recomendaciones:
            recomendaciones.append('Distribución de intensidades óptima')

        return recomendaciones

    def _calcular_carga_dia(self, entreno):
        """
        Calcula carga de entrenamiento de un día
        """
        if not entreno.notas_liftin:
            return 50  # Carga base estimada

        ejercicios = parsear_ejercicios(entreno.notas_liftin)
        volumen = self._calcular_volumen_entreno(ejercicios)
        intensidad = self._estimar_intensidad_entreno(ejercicios)
        duracion = entreno.duracion_minutos or 60

        # Fórmula de carga: (Volumen × Intensidad × Duración) / 1000
        carga = (volumen * intensidad * duracion) / 10000

        return max(carga, 10)  # Mínimo 10 puntos de carga

    def _evaluar_nivel_fatiga(self, fatiga_actual):
        """
        Evalúa nivel de fatiga actual
        """
        if fatiga_actual < 50:
            return 'baja'
        elif fatiga_actual < 100:
            return 'moderada'
        elif fatiga_actual < 150:
            return 'alta'
        else:
            return 'critica'

    def _calcular_dias_recuperacion(self, fatiga_actual):
        """
        Calcula días de recuperación necesarios
        """
        if fatiga_actual < 50:
            return 1
        elif fatiga_actual < 100:
            return 2
        elif fatiga_actual < 150:
            return 3
        else:
            return 5

    def _generar_recomendacion_descanso(self, nivel_fatiga, dias_recuperacion):
        """
        Genera recomendación de descanso
        """
        recomendaciones = {
            'baja': 'Fatiga baja. Puedes continuar con el entrenamiento normal.',
            'moderada': f'Fatiga moderada. Considera {dias_recuperacion} días de entrenamiento ligero.',
            'alta': f'Fatiga alta. Toma {dias_recuperacion} días de descanso activo o completo.',
            'critica': f'Fatiga crítica. Descanso obligatorio de {dias_recuperacion} días mínimo.'
        }

        return recomendaciones.get(nivel_fatiga, 'Evalúa tu estado de recuperación.')

    def _calcular_intensidad_promedio(self, ejercicios):
        """
        Calcula intensidad promedio de una lista de ejercicios
        """
        intensidades = []

        for ejercicio in ejercicios:
            try:
                reps = self._extraer_repeticiones(ejercicio.get('repeticiones', '1'))

                # Estimar intensidad basada en repeticiones
                if reps <= 3:
                    intensidad = 90
                elif reps <= 6:
                    intensidad = 85
                elif reps <= 12:
                    intensidad = 75
                else:
                    intensidad = 60

                intensidades.append(intensidad)
            except (ValueError, TypeError):
                continue

        return sum(intensidades) / len(intensidades) if intensidades else 70

    def _extraer_repeticiones(self, rep_str):
        """
        Extrae número de repeticiones de string como "3x8"
        """
        try:
            rep_str = str(rep_str).lower().replace('×', 'x').replace(' ', '')
            if 'x' in rep_str:
                return int(rep_str.split('x')[1])
            return int(rep_str)
        except:
            return 1

    def _extraer_series(self, rep_str):
        """
        Extrae número de series de string como "3x8"
        """
        try:
            rep_str = str(rep_str).lower().replace('×', 'x').replace(' ', '')
            if 'x' in rep_str:
                return int(rep_str.split('x')[0])
            return 1
        except:
            return 1


# Vista para el Dashboard de Intensidad Avanzado - VERSIÓN DE DEPURACIÓN

def dashboard_intensidad_avanzado(request, cliente_id):
    """
    Vista principal del Dashboard de Intensidad Avanzado.
    - CON LIMPIEZA DE CACHE FORZADA PARA DEPURACIÓN.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    analizador = AnalisisIntensidadAvanzado(cliente)

    # --- LÓGICA DE DEPURACIÓN ---
    # Forzamos la eliminación del cache en cada carga para asegurarnos
    # de que todos los cálculos se hacen desde cero.
    cache_key = f'dashboard_intensidad_{cliente.id}'
    cache.delete(cache_key)
    logger.info(f"¡CACHE FORZADO A LIMPIAR PARA '{cache_key}'!")
    # --- FIN DE LÓGICA DE DEPURACIÓN ---

    # El resto de la vista ahora se ejecutará siempre con datos frescos.

    periodo = int(request.GET.get('periodo', 30))

    # Como el cache está limpio, estas líneas siempre se ejecutarán
    logger.info(f"Calculando todos los datos para el cliente {cliente.id} (sin cache).")
    zonas_entrenamiento = analizador.analizar_zonas_entrenamiento(periodo_dias=30)
    analisis_carga = analizador.analizar_carga_entrenamiento(periodo_dias=90)
    distribucion_intensidades = analizador.analizar_distribucion_intensidades(periodo_dias=60)

    # El cálculo de fatiga también se ejecuta
    fatiga_acumulada = analizador.calcular_fatiga_acumulada(periodo_dias=14)
    logger.info(f"FATIGA CALCULADA: {fatiga_acumulada}")  # <-- Log para ver el resultado

    # Construcción del contexto
    context = {
        'cliente': cliente,
        'periodo': periodo,
        'zonas_entrenamiento': zonas_entrenamiento,
        'analisis_carga': analisis_carga,
        'distribucion_intensidades': distribucion_intensidades,
        'fatiga_acumulada': fatiga_acumulada,
    }

    # Preparar datos para JS
    datos_graficos = {
        'zonas': {
            'labels': list(context['zonas_entrenamiento']['distribucion'].keys()),
            'valores': [d['porcentaje'] for d in context['zonas_entrenamiento']['distribucion'].values()],
            'colores': ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
        },
        'carga': {
            'carga_semanal': context['analisis_carga']['carga_semanal']
        },
        'intensidades': {
            'distribucion': context['distribucion_intensidades']['distribucion']
        }
    }
    context['datos_graficos'] = json.dumps(datos_graficos)

    return render(request, 'analytics/intensidad_avanzado.html', context)
