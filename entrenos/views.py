from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from analytics.sistema_educacion_helms import agregar_educacion_a_plan

from collections import defaultdict
from analytics.monitor_adherencia import MonitorAdherencia, SesionEntrenamiento
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
from analytics.planificador_helms_completo import PlanificadorHelms, crear_perfil_desde_cliente
from typing import Dict
from django.core.serializers.json import DjangoJSONEncoder
from .models import LogroDesbloqueado, EstadoEmocional
from decimal import Decimal
from .forms import ImportarLiftinCompletoForm
from joi.utils import generar_respuesta_joi
from .forms import (
    SeleccionClienteForm,
    DetalleEjercicioForm,
    FiltroClienteForm,
    BuscarEntrenamientosLiftinForm,  # ← AGREGAR ESTA LÍNEA
    ImportarLiftinCompletoForm,
    ImportarLiftinBasicoForm,
    ExportarDatosForm
)
from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _
from types import SimpleNamespace
import copy
from types import SimpleNamespace
from django.shortcuts import render, get_object_or_404
from .models import EntrenoRealizado, SerieRealizada
from django.db.models import Count, Avg, Sum
import json
from .forms import EjercicioForm
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from decimal import Decimal, getcontext
from datetime import date
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django import forms
from django.db.models import Avg, Sum
from django.db import transaction
from rutinas.models import Rutina, RutinaEjercicio
from clientes.models import Cliente
from .models import EntrenoRealizado, SerieRealizada, PlanPersonalizado
from .forms import SeleccionClienteForm, DetalleEjercicioForm, FiltroClienteForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import EntrenoRealizado, SerieRealizada
from django.db.models import Count, Avg, Sum

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import logging

# Archivo: entrenos/views.py - VISTAS PARA LIFTIN

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from .gamificacion_service import EntrenamientoGamificacionService
from .models import EntrenoRealizado, DatosLiftinDetallados
# from .forms import ImportarLiftinForm, BuscarEntrenamientosForm, ExportarDatosForm
from clientes.models import Cliente

from django.db.models import Avg

from django.shortcuts import render
from entrenos.models import DetalleEjercicioRealizado

from django.shortcuts import render
from entrenos.models import EntrenoRealizado
from entrenos.utils.utils import parse_reps_and_series  # crea este archivo o añade allí la función

from django.shortcuts import render
from .models import EntrenoRealizado
from entrenos.utils.utils import \
    parsear_ejercicios_de_notas  # si lo pones en un archivo aparte, si no, define ahí mismo

from django.shortcuts import render
from entrenos.models import EntrenoRealizado

from collections import Counter

from django.shortcuts import render

from collections import Counter
from django.core.paginator import Paginator
from entrenos.models import EntrenoRealizado
from entrenos.utils.utils import parse_reps_and_series
from django.shortcuts import render

from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from entrenos.utils.utils import normalizar_nombre_ejercicio
from analytics.planificador import PlanificadorAvanzadoHelms, generar_contexto_calendario
from analytics.views import CalculadoraEjerciciosTabla


def detalle_ejercicio(request, nombre):
    registros = []
    nombre_normalizado = normalizar_nombre_ejercicio(nombre)

    entrenos = EntrenoRealizado.objects.exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

    for entreno in entrenos:
        ejercicios = parsear_ejercicios(entreno.notas_liftin)
        for e in ejercicios:
            if normalizar_nombre_ejercicio(e["nombre"]) == nombre_normalizado:
                e["fecha"] = entreno.fecha
                e["cliente"] = getattr(entreno.cliente, 'nombre', str(entreno.cliente))
                try:
                    e["peso_float"] = float(str(e["peso"]).replace(",", "."))
                except:
                    e["peso_float"] = None
                registros.append(e)

    registros = sorted(registros, key=lambda x: x["fecha"])

    return render(request, "entrenos/detalle_ejercicio.html", {
        "nombre": nombre_normalizado,
        "registros": registros
    })


def ejercicios_realizados_view(request):
    filtro = request.GET.get('filtro')
    if filtro:
        filtro = filtro.strip().title()

    ejercicios = []
    contador = Counter()

    entrenos = EntrenoRealizado.objects.exclude(notas_liftin__isnull=True).exclude(notas_liftin='').order_by('-fecha')

    for entreno in entrenos:
        ejercicios_parsed = parsear_ejercicios(entreno.notas_liftin)
        for e in ejercicios_parsed:
            e['fecha'] = entreno.fecha
            e['cliente'] = getattr(entreno.cliente, 'nombre', str(entreno.cliente))
            if not filtro or e['nombre'] == filtro:
                ejercicios.append(e)
            nombre_normalizado = e['nombre'].strip().title()  # Ejemplo: "press banca" → "Press Banca"
            e['nombre'] = nombre_normalizado
            contador[nombre_normalizado] += 1

    ejercicios_mas_realizados = sorted(
        [{'nombre': nombre, 'veces': veces} for nombre, veces in contador.items()],
        key=lambda x: x['veces'],
        reverse=True
    )

    # ✅ paginar todos los ejercicios (10 por página)
    paginator = Paginator(ejercicios, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # === Tabla de mayor peso por ejercicio ===
    def convertir_peso(p):
        try:
            return float(str(p).replace(",", "."))
        except:
            return None

    # Clonar para evitar modificar el original
    ejercicios_para_max = ejercicios.copy()
    for e in ejercicios_para_max:
        e["peso_float"] = convertir_peso(e["peso"])

    # Filtrar válidos y quedarnos con el de mayor peso por nombre
    mayores_por_ejercicio = {}
    for e in ejercicios_para_max:
        if e["peso_float"] is None:
            continue
        nombre = e["nombre"]
        if nombre not in mayores_por_ejercicio or e["peso_float"] > mayores_por_ejercicio[nombre]["peso_float"]:
            mayores_por_ejercicio[nombre] = e

    mayores_list = sorted(mayores_por_ejercicio.values(), key=lambda x: x["nombre"])

    return render(request, 'entrenos/tabla_ejercicios.html', {
        'ejercicios': page_obj,
        'page_obj': page_obj,
        'ejercicios_mas_realizados': ejercicios_mas_realizados,
        'filtro': filtro,
        'mayores_por_ejercicio': mayores_list,
    })


@login_required
def dashboard_liftin(request):
    """
    Dashboard principal para datos de Liftin
    """
    # Estadísticas generales
    total_entrenamientos = EntrenoRealizado.objects.count()
    entrenamientos_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin').count()
    entrenamientos_manual = EntrenoRealizado.objects.filter(fuente_datos='manual').count()

    # Estadísticas de Liftin
    stats_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin').aggregate(
        total_duracion=Sum('duracion_minutos'),
        total_calorias=Sum('calorias_quemadas'),
        fc_promedio=Avg('frecuencia_cardiaca_promedio')
    )

    # Entrenamientos recientes
    entrenamientos_recientes = EntrenoRealizado.objects.select_related(
        'cliente', 'rutina'
    ).order_by('-fecha')[:10]

    # Datos para gráficos (últimos 30 días)
    fecha_limite = timezone.now().date() - timedelta(days=30)
    entrenamientos_por_dia = EntrenoRealizado.objects.filter(
        fecha__gte=fecha_limite
    ).values('fecha', 'fuente_datos').annotate(
        count=Count('id')
    ).order_by('fecha')

    context = {
        'total_entrenamientos': total_entrenamientos,
        'entrenamientos_liftin': entrenamientos_liftin,
        'entrenamientos_manual': entrenamientos_manual,
        'stats_liftin': stats_liftin,
        'entrenamientos_recientes': entrenamientos_recientes,
        'entrenamientos_por_dia': list(entrenamientos_por_dia),
    }

    return render(request, 'entrenos/dashboard_liftin.html', context)


from rutinas.models import Programa, Rutina


@login_required
def importar_liftin(request):
    if request.method == 'POST':
        form = ImportarLiftinForm(request.POST)
        if form.is_valid():
            entrenamiento = form.save(commit=False)

            # Asegurar que haya un programa por defecto
            programa, creado = Programa.objects.get_or_create(nombre="Importado de Liftin")

            # Crear una rutina asociada si es necesario
            rutina = Rutina.objects.create(
                nombre=form.cleaned_data['nombre_rutina_liftin'],
                cliente=form.cleaned_data['cliente'],
                programa=programa,
                orden=1
            )

            entrenamiento.rutina = rutina
            entrenamiento.save()

            messages.success(request, "Entrenamiento importado exitosamente desde Liftin.")
            return redirect('entrenos:dashboard_liftin')
    else:
        form = ImportarLiftinCompletoForm()

    return render(request, 'entrenos/importar_liftin.html', {'form': form})


@login_required
def lista_entrenamientos(request):
    """
    Vista para listar entrenamientos con búsqueda
    """
    # CORRECCIÓN: Usar el formulario correcto
    form = BuscarEntrenamientosLiftinForm(request.GET or None)

    entrenamientos = EntrenoRealizado.objects.all().order_by('-fecha')

    if form and form.is_valid():
        # Aplicar filtros del formulario
        if form.cleaned_data.get('cliente'):
            entrenamientos = entrenamientos.filter(cliente=form.cleaned_data['cliente'])

        if form.cleaned_data.get('fuente_datos'):
            entrenamientos = entrenamientos.filter(fuente_datos=form.cleaned_data['fuente_datos'])

        if form.cleaned_data.get('fecha_desde'):
            entrenamientos = entrenamientos.filter(fecha__gte=form.cleaned_data['fecha_desde'])

        if form.cleaned_data.get('fecha_hasta'):
            entrenamientos = entrenamientos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])

    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(entrenamientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'entrenamientos': page_obj,
        'title': 'Lista de Entrenamientos'
    }

    return render(request, 'entrenos/lista_entrenamientos.html', context)


@login_required
def detalle_entrenamiento(request, entrenamiento_id):
    """
    Vista detallada de un entrenamiento
    """
    entrenamiento = get_object_or_404(EntrenoRealizado, id=entrenamiento_id)

    # Obtener datos adicionales de Liftin si existen
    datos_liftin = None
    if hasattr(entrenamiento, 'datos_liftin'):
        datos_liftin = entrenamiento.datos_liftin

    context = {
        'entrenamiento': entrenamiento,
        'datos_liftin': datos_liftin,
    }

    return render(request, 'entrenos/detalle_entrenamiento.html', context)


@login_required
def estadisticas_liftin(request):
    """
    Vista para mostrar estadísticas específicas de Liftin
    """
    from django.db.models import Count, Sum, Avg

    # CORRECCIÓN: Usar nombres de campos correctos
    entrenamientos_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin')
    entrenamientos_manual = EntrenoRealizado.objects.filter(fuente_datos='manual')

    # Estadísticas básicas
    stats = {
        'total_liftin': entrenamientos_liftin.count(),
        'total_manual': entrenamientos_manual.count(),
        'total_general': EntrenoRealizado.objects.count(),
    }

    # Estadísticas de Liftin
    stats_liftin = entrenamientos_liftin.aggregate(
        volumen_total=Sum('volumen_total_kg'),
        calorias_total=Sum('calorias_quemadas'),
        duracion_promedio=Avg('duracion_minutos'),
        ejercicios_promedio=Avg('numero_ejercicios'),
        fc_promedio=Avg('frecuencia_cardiaca_promedio')
    )

    # Estadísticas por cliente
    stats_por_cliente = entrenamientos_liftin.values('cliente__nombre').annotate(
        total=Count('id'),
        volumen=Sum('volumen_total_kg')
    ).order_by('-total')[:10]

    # Entrenamientos recientes
    entrenamientos_recientes = entrenamientos_liftin.order_by('-fecha', '-hora_inicio')[:10]

    context = {
        'stats': stats,
        'stats_liftin': stats_liftin,
        'stats_por_cliente': stats_por_cliente,
        'entrenamientos_recientes': entrenamientos_recientes,
        'title': 'Estadísticas de Liftin'
    }

    return render(request, 'entrenos/estadisticas_liftin.html', context)


@login_required
def exportar_datos(request):
    """
    Vista para exportar datos de entrenamientos
    """
    if request.method == 'POST':
        form = ExportarDatosForm(request.POST)
        if form.is_valid():
            # Construir queryset basado en filtros
            entrenamientos = EntrenoRealizado.objects.select_related('cliente', 'rutina')

            # Aplicar filtros
            incluir = form.cleaned_data['incluir']
            if incluir == 'solo_liftin':
                entrenamientos = entrenamientos.filter(fuente_datos='liftin')
            elif incluir == 'solo_manual':
                entrenamientos = entrenamientos.filter(fuente_datos='manual')

            if form.cleaned_data['cliente']:
                entrenamientos = entrenamientos.filter(cliente=form.cleaned_data['cliente'])

            if form.cleaned_data['fecha_desde']:
                entrenamientos = entrenamientos.filter(fecha__gte=form.cleaned_data['fecha_desde'])

            if form.cleaned_data['fecha_hasta']:
                entrenamientos = entrenamientos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])

            # Exportar según formato
            formato = form.cleaned_data['formato']
            if formato == 'csv':
                return exportar_csv(entrenamientos)
            elif formato == 'json':
                return exportar_json(entrenamientos)
    else:
        form = ExportarDatosForm()

    context = {
        'form': form,
    }

    return render(request, 'entrenos/exportar_datos.html', context)


def exportar_csv(entrenamientos):
    """
    Exporta entrenamientos a formato CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="entrenamientos_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    # Cabeceras
    writer.writerow([
        'Cliente',
        'Rutina',
        'Fecha',
        'Fuente',
        'Duración (min)',
        'Calorías',
        'FC Promedio',
        'FC Máxima',
        'Notas'
    ])

    # Datos
    for entreno in entrenamientos:
        writer.writerow([
            entreno.cliente.nombre,
            entreno.rutina.nombre,
            entreno.fecha.strftime('%Y-%m-%d'),
            entreno.get_fuente_datos_display(),
            entreno.duracion_minutos or '',
            entreno.calorias_quemadas or '',
            entreno.frecuencia_cardiaca_promedio or '',
            entreno.frecuencia_cardiaca_maxima or '',
            entreno.notas_liftin or ''
        ])

    return response


def exportar_json(entrenamientos):
    """
    Exporta entrenamientos a formato JSON
    """
    data = []

    for entreno in entrenamientos:
        data.append({
            'id': entreno.id,
            'cliente': entreno.cliente.nombre,
            'rutina': entreno.rutina.nombre,
            'fecha': entreno.fecha.isoformat(),
            'fuente_datos': entreno.fuente_datos,
            'duracion_minutos': entreno.duracion_minutos,
            'calorias_quemadas': entreno.calorias_quemadas,
            'frecuencia_cardiaca_promedio': entreno.frecuencia_cardiaca_promedio,
            'frecuencia_cardiaca_maxima': entreno.frecuencia_cardiaca_maxima,
            'notas_liftin': entreno.notas_liftin,
            'liftin_workout_id': entreno.liftin_workout_id,
            'fecha_importacion': entreno.fecha_importacion.isoformat() if entreno.fecha_importacion else None
        })

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="entrenamientos_{timezone.now().strftime("%Y%m%d")}.json"'

    return response


@login_required
def api_stats_dashboard(request):
    """
    API endpoint para obtener estadísticas para el dashboard
    """
    # Datos para gráficos de los últimos 30 días
    fecha_limite = timezone.now().date() - timedelta(days=30)

    # Entrenamientos por día
    entrenamientos_por_dia = []
    for i in range(30):
        fecha = fecha_limite + timedelta(days=i)
        manual = EntrenoRealizado.objects.filter(fecha=fecha, fuente_datos='manual').count()
        liftin = EntrenoRealizado.objects.filter(fecha=fecha, fuente_datos='liftin').count()

        entrenamientos_por_dia.append({
            'fecha': fecha.isoformat(),
            'manual': manual,
            'liftin': liftin,
            'total': manual + liftin
        })

    # Distribución por fuente
    distribucion = {
        'manual': EntrenoRealizado.objects.filter(fuente_datos='manual').count(),
        'liftin': EntrenoRealizado.objects.filter(fuente_datos='liftin').count()
    }

    data = {
        'entrenamientos_por_dia': entrenamientos_por_dia,
        'distribucion': distribucion
    }

    return JsonResponse(data)


def entrenos_filtrados(request, rango):
    """
    Filtra los entrenamientos realizados según diferentes rangos temporales.

    Args:
        request: Objeto HttpRequest
        rango: Cadena que indica el rango temporal ('hoy', 'semana', 'mes', 'anio', o cualquier otro valor para todos)

    Returns:
        HttpResponse con la plantilla renderizada
    """
    hoy = date.today()

    if rango == "hoy":
        queryset = EntrenoRealizado.objects.filter(fecha=hoy)
        titulo = "Entrenamientos de hoy"
    elif rango == "semana":
        inicio = hoy - timedelta(days=hoy.weekday())
        queryset = EntrenoRealizado.objects.filter(fecha__gte=inicio)
        titulo = "Entrenamientos de esta semana"
    elif rango == "mes":
        inicio = hoy.replace(day=1)
        queryset = EntrenoRealizado.objects.filter(fecha__gte=inicio)
        titulo = "Entrenamientos de este mes"
    elif rango == "anio":
        inicio = hoy.replace(month=1, day=1)
        queryset = EntrenoRealizado.objects.filter(fecha__gte=inicio)
        titulo = "Entrenamientos de este año"
    else:
        queryset = EntrenoRealizado.objects.all()
        titulo = "Todos los entrenamientos"

    queryset = queryset.select_related('cliente', 'rutina').order_by('-fecha')

    return render(request, 'entrenos/entrenos_filtrados.html', {
        'entrenos': queryset,
        'titulo': titulo
    })


def historial_entrenos(request):
    """
    Muestra un historial de entrenamientos con posibilidad de filtrar por cliente.

    Args:
        request: Objeto HttpRequest

    Returns:
        HttpResponse con la plantilla renderizada
    """
    from django.core.paginator import Paginator

    form = FiltroClienteForm(request.GET or None)
    entrenos = EntrenoRealizado.objects.select_related('cliente', 'rutina').prefetch_related('series__ejercicio')

    if form.is_valid() and form.cleaned_data['cliente']:
        cliente = form.cleaned_data['cliente']
        entrenos = entrenos.filter(cliente=cliente)
    else:
        cliente = None

    entrenos = entrenos.order_by('-fecha')

    # Agregar atributo .perfecto a cada entreno
    for entreno in entrenos:
        total = entreno.series.count()
        completadas = entreno.series.filter(completado=True).count()
        entreno.perfecto = total > 0 and completadas == total

        # Formatear fecha como "26 de mayo de 2025"
        df = DateFormat(entreno.fecha)
        entreno.fecha_formateada = df.format("j \\d\\e F \\d\\e Y")
    # Paginación
    paginator = Paginator(entrenos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'entrenos/vista_historial_detallado.html', {
        'entrenos': page_obj,
        'form': form,
        'cliente': cliente,
        'page_obj': page_obj,
    })


def crear_entreno(entreno, ejercicios_forms, request, cliente, rutina):
    """
    Crea un nuevo entrenamiento con sus series realizadas.

    Args:
        entreno: Objeto EntrenoRealizado
        ejercicios_forms: Lista de tuplas (ejercicio, form)
        request: Objeto HttpRequest
        cliente: Objeto Cliente
        rutina: Objeto Rutina

    Returns:
        None
    """
    for ejercicio, _ in ejercicios_forms:
        i = 1
        while True:
            reps_key = f"{ejercicio.id}_reps_{i}"
            peso_key = f"{ejercicio.id}_peso_{i}"
            completado_key = f"{ejercicio.id}_completado_{i}"

            try:
                reps = request.POST.get(reps_key)
                peso = request.POST.get(peso_key)
                completado = request.POST.get(completado_key) == "1"

                if reps is None or peso is None:
                    break

                if reps.strip() == '' and peso.strip() == '':
                    i += 1
                    continue

                SerieRealizada.objects.create(
                    entreno=entreno,
                    ejercicio=ejercicio,
                    serie_numero=i,
                    repeticiones=int(reps),
                    peso_kg=float(peso.replace(',', '.')),
                    completado=completado
                )
                print(
                    f"Serie creada: {ejercicio.nombre}, Serie {i}, Reps: {reps}, Peso: {peso}, Completado: {completado}")
            except (ValueError, TypeError) as e:
                messages.error(request, f"⚠️ Error al procesar serie {i} de {ejercicio.nombre}: {str(e)}")
                break

            i += 1


from django.db import transaction
from decimal import Decimal

from datetime import date
from django.core.serializers.json import DjangoJSONEncoder

from decimal import Decimal, getcontext
from datetime import date
from django.core.serializers.json import DjangoJSONEncoder

from decimal import Decimal, getcontext
from django.db import transaction

from decimal import Decimal, getcontext
from django.db import transaction


def adaptar_plan_personalizado(entreno, ejercicios_forms, cliente, rutina, request):
    """
    Versión final con reinicio de contador después de reducción
    """
    # Configurar precisión decimal
    getcontext().prec = 8

    with transaction.atomic():
        try:
            cliente_real = Cliente.objects.get(id=entreno.cliente_id)
            print(f"\nProcesando cliente: {cliente_real.nombre}")
        except Exception as e:
            print(f"❌ Error al obtener cliente: {str(e)}")
            return

        # Inicializar estructuras de seguimiento
        session_key = f'adaptacion_{cliente_real.id}_{rutina.id}'
        if session_key not in request.session:
            request.session[session_key] = {}

        datos_adaptacion = request.session[session_key]

        for ejercicio, _ in ejercicios_forms:
            try:
                ejercicio_obj = ejercicio if isinstance(ejercicio, Ejercicio) else Ejercicio.objects.get(id=ejercicio)
                ejercicio_id = str(ejercicio_obj.id)

                print(f"\n--- Procesando ejercicio: {ejercicio_obj.nombre} ---")

                # Obtener o inicializar registro para este ejercicio
                if ejercicio_id not in datos_adaptacion:
                    datos_adaptacion[ejercicio_id] = {
                        'nombre': ejercicio_obj.nombre,
                        'fallos_consecutivos': 0,
                        'historial': []
                    }

                registro = datos_adaptacion[ejercicio_id]

                # Obtener configuración actual del ejercicio
                try:
                    asignacion = RutinaEjercicio.objects.get(
                        rutina=rutina,
                        ejercicio=ejercicio_obj
                    )
                    plan, created = PlanPersonalizado.objects.get_or_create(
                        cliente=cliente_real,
                        ejercicio=ejercicio_obj,
                        rutina=rutina,
                        defaults={
                            'repeticiones_objetivo': asignacion.repeticiones,
                            'peso_objetivo': Decimal(str(asignacion.peso_kg))
                        }
                    )
                except RutinaEjercicio.DoesNotExist:
                    print(f"No hay asignación para {ejercicio_obj.nombre} en esta rutina")
                    continue

                # Guardar peso anterior antes de cualquier modificación
                peso_anterior = Decimal(str(plan.peso_objetivo))
                print(f"Peso actual: {float(peso_anterior)}kg")
                print(f"Fallos consecutivos actuales: {registro['fallos_consecutivos']}")

                # Analizar rendimiento
                series = SerieRealizada.objects.filter(
                    entreno=entreno,
                    ejercicio=ejercicio_obj
                )
                total_series = series.count()

                if total_series == 0:
                    print("No hay series registradas")
                    continue

                series_completadas = sum(
                    1 for s in series
                    if s.completado and s.repeticiones >= plan.repeticiones_objetivo
                )
                porcentaje_exito = float(series_completadas) / float(total_series)
                fue_exitoso = porcentaje_exito >= 0.8

                # Calcular peso promedio del entreno actual
                peso_promedio = sum(Decimal(str(s.peso_kg)) for s in series) / Decimal(str(total_series))
                print(f"Peso promedio en este entreno: {float(peso_promedio)}kg")

                # Actualizar historial de rendimiento
                registro['historial'].append({
                    'fecha': entreno.fecha.isoformat(),
                    'porcentaje_exito': porcentaje_exito,
                    'peso_promedio': float(peso_promedio),
                    'fue_exitoso': fue_exitoso
                })
                registro['historial'] = registro['historial'][-3:]  # Mantener solo últimos 3

                # Lógica de adaptación
                if fue_exitoso:
                    # Aumentar peso y reiniciar contador
                    nuevo_peso = (peso_anterior * Decimal('1.10')).quantize(Decimal('0.1'))
                    plan.peso_objetivo = nuevo_peso
                    plan.save()
                    registro['fallos_consecutivos'] = 0  # Reiniciar contador

                    print(f"✅ ÉXITO - Peso aumentado a {float(nuevo_peso)}kg | Contador reiniciado")

                    if 'adaptaciones_positivas' not in request.session:
                        request.session['adaptaciones_positivas'] = []
                    request.session['adaptaciones_positivas'].append({
                        'ejercicio_id': ejercicio_obj.id,
                        'nombre': ejercicio_obj.nombre,
                        'peso_anterior': float(peso_anterior),
                        'nuevo_peso': float(nuevo_peso)
                    })
                else:
                    # Incrementar contador de fallos
                    registro['fallos_consecutivos'] += 1
                    print(f"❌ FALLO - Conteo actual: {registro['fallos_consecutivos']}/3")

                    # Verificar si aplica reducción
                    if registro['fallos_consecutivos'] >= 3:
                        nuevo_peso = (peso_promedio * Decimal('0.90')).quantize(Decimal('0.1'))
                        plan.peso_objetivo = nuevo_peso
                        plan.save()
                        registro['fallos_consecutivos'] = 0  # Reiniciar contador después de reducción

                        print(f"🔽 REDUCCIÓN APLICADA - Nuevo peso: {float(nuevo_peso)}kg | Contador reiniciado")

                        if 'adaptaciones_negativas' not in request.session:
                            request.session['adaptaciones_negativas'] = []
                        request.session['adaptaciones_negativas'].append({
                            'ejercicio_id': ejercicio_obj.id,
                            'nombre': ejercicio_obj.nombre,
                            'peso_anterior': float(peso_promedio),
                            'nuevo_peso': float(nuevo_peso),
                            'razon': '3 fallos consecutivos'
                        })

                # Actualizar sesión
                request.session.modified = True

            except Exception as e:
                print(
                    f"Error procesando {ejercicio_obj.nombre if 'ejercicio_obj' in locals() else 'UNKNOWN'}: {str(e)}")
                continue


def actualizar_rutina_cliente(cliente, rutina):
    """
    Actualiza la rutina actual del cliente al completar un entrenamiento.

    Args:
        cliente: Objeto Cliente
        rutina: Objeto Rutina

    Returns:
        tuple: (bool, str) - Éxito y mensaje
    """
    try:
        rutinas_ordenadas = cliente.programa.rutinas.order_by('orden')
        rutinas = list(rutinas_ordenadas)

        if not rutinas:
            return False, "No hay rutinas disponibles"

        try:
            index = rutinas.index(rutina)
            siguiente = rutinas[(index + 1) % len(rutinas)]
            cliente.rutina_actual = siguiente
            cliente.save()

            if siguiente == rutinas[0]:
                return True, f"¡Ciclo completado! Se reinicia con: {siguiente.nombre}"
            else:
                return True, f"Se asignó la siguiente rutina: {siguiente.nombre}"
        except (ValueError, ZeroDivisionError):
            return False, "No se pudo determinar la siguiente rutina"
    except Exception as e:
        return False, f"Error al actualizar rutina: {str(e)}"


def empezar_entreno(request, rutina_id):
    """
    Muestra el formulario para empezar un entrenamiento con manejo seguro de valores decimales.
    Versión final adaptada para procesar correctamente los datos del formulario según el formato
    de la plantilla actual, sin necesidad de modificar la plantilla HTML.

    Args:
        request: Objeto HttpRequest
        rutina_id: ID de la rutina

    Returns:
        HttpResponse con la plantilla renderizada
    """
    from decimal import Decimal, InvalidOperation
    import logging
    from django.db import connection

    # Configurar logging para depuración
    logger = logging.getLogger(__name__)

    # Obtener rutina directamente (sin prefetch_related para evitar errores)
    try:
        rutina = get_object_or_404(Rutina, id=rutina_id)
        # Cargar ejercicios de forma segura con SQL directo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT re.id, re.rutina_id, re.ejercicio_id, re.series, re.repeticiones, re.peso_kg, 
                       e.id as ej_id, e.nombre as ej_nombre, e.grupo_muscular, e.equipo
                FROM rutinas_rutinaejercicio re
                JOIN rutinas_ejercicio e ON re.ejercicio_id = e.id
                WHERE re.rutina_id = %s
            """, [rutina_id])
            columns = [col[0] for col in cursor.description]
            ejercicios_rutina = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error al obtener rutina y ejercicios: {str(e)}")
        messages.error(request, "Error al cargar la rutina. Por favor, inténtalo de nuevo.")
        return redirect('hacer_entreno')

    cliente_id = request.GET.get('cliente_id')
    cliente_inicial = None

    if cliente_id and cliente_id.isdigit():
        try:
            cliente_inicial = Cliente.objects.get(id=int(cliente_id))
        except Cliente.DoesNotExist:
            cliente_inicial = None

    ejercicios_forms = []
    cliente_form = None
    datos_previos = {}
    fallos_anteriores = set()

    if request.method == 'POST':
        cliente_form = SeleccionClienteForm(request.POST)

        # IMPORTANTE: Procesar los datos del POST según el formato de la plantilla
        if cliente_form.is_valid():
            cliente = cliente_form.cleaned_data['cliente']

            # Validar cliente
            if not isinstance(cliente, Cliente):
                try:
                    cliente = Cliente.objects.get(id=int(cliente))
                except (ValueError, Cliente.DoesNotExist, TypeError):
                    messages.error(request, "⚠️ Cliente inválido. No se puede continuar.")
                    return redirect('hacer_entreno')

            # Crear entreno
            entreno = EntrenoRealizado.objects.create(cliente=cliente, rutina=rutina)

            # IMPORTANTE: Procesar los datos del formulario según el formato de la plantilla
            try:
                # Procesar cada ejercicio de la rutina
                for asignacion in ejercicios_rutina:
                    ejercicio_id = asignacion['ejercicio_id']
                    ej_id = asignacion['ej_id']

                    # Contar cuántas series hay para este ejercicio
                    series_count = 0
                    for key in request.POST.keys():
                        if key.startswith(f"{ej_id}_reps_"):
                            series_count += 1

                    # Si no hay series, continuar con el siguiente ejercicio
                    if series_count == 0:
                        continue

                    # Procesar cada serie
                    for i in range(1, series_count + 1):
                        try:
                            # Obtener datos de la serie
                            reps_key = f"{ej_id}_reps_{i}"
                            peso_key = f"{ej_id}_peso_{i}"
                            completado_key = f"{ej_id}_completado_{i}"

                            # Obtener valores con manejo seguro
                            repeticiones = 0
                            if reps_key in request.POST:
                                try:
                                    repeticiones = int(request.POST[reps_key])
                                except (ValueError, TypeError):
                                    repeticiones = 0

                            peso_kg = 0.0
                            if peso_key in request.POST:
                                try:
                                    peso_kg = float(request.POST[peso_key])
                                except (ValueError, TypeError, InvalidOperation):
                                    try:
                                        valor_str = str(request.POST[peso_key]).replace(',', '.')
                                        valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                                        if valor_limpio:
                                            peso_kg = float(valor_limpio)
                                    except:
                                        peso_kg = 0.0

                            completado = False
                            if completado_key in request.POST:
                                completado = request.POST[completado_key] == "1"

                            # Crear serie realizada
                            SerieRealizada.objects.create(
                                entreno=entreno,
                                ejercicio_id=ejercicio_id,  # Usar ID, no objeto
                                serie_numero=i,
                                repeticiones=repeticiones,
                                peso_kg=peso_kg,
                                completado=completado
                            )
                        except Exception as e:
                            logger.error(f"Error al crear serie {i} para ejercicio {asignacion['ej_nombre']}: {str(e)}")

                # Adaptar plan personalizado
                adaptar_plan_personalizado(entreno, [(Ejercicio.objects.get(id=a['ejercicio_id']), None) for a in
                                                     ejercicios_rutina], cliente, rutina, request)

                # Actualizar rutina del cliente
                exito, mensaje = actualizar_rutina_cliente(cliente, rutina)

                # Mostrar mensaje de éxito
                messages.success(request, "✅ Entreno guardado con éxito.")
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.warning(request, mensaje)

                return redirect('resumen_entreno', entreno_id=entreno.id)
            except Exception as e:
                logger.error(f"Error general al procesar formulario: {str(e)}")
                messages.error(request, f"Error al guardar el entreno: {str(e)}")
                # Continuar con la renderización del formulario
    else:
        cliente_form = SeleccionClienteForm(initial={'cliente': cliente_inicial})

        if cliente_form is not None:
            cliente_form.fields['cliente'].widget = forms.HiddenInput()

        # Obtener datos previos si hay cliente inicial - Manejo seguro con SQL directo
        if cliente_inicial:
            try:
                # Obtener último entreno con SQL directo para evitar errores de conversión
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, fecha
                        FROM entrenos_entrenorealizado
                        WHERE cliente_id = %s AND rutina_id = %s
                        ORDER BY fecha DESC, id DESC
                        LIMIT 1
                    """, [cliente_inicial.id, rutina_id])
                    ultimo_entreno_row = cursor.fetchone()

                if ultimo_entreno_row:
                    ultimo_entreno_id = ultimo_entreno_row[0]

                    # Obtener series con SQL directo
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT sr.id, sr.entreno_id, sr.ejercicio_id, sr.serie_numero, 
                                   sr.repeticiones, sr.peso_kg, sr.completado,
                                   e.id as ej_id, e.nombre as ej_nombre
                            FROM entrenos_serierealizada sr
                            JOIN rutinas_ejercicio e ON sr.ejercicio_id = e.id
                            WHERE sr.entreno_id = %s
                        """, [ultimo_entreno_id])
                        columns = [col[0] for col in cursor.description]
                        series_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                    # Procesar series de forma segura
                    for serie in series_rows:
                        try:
                            ejercicio_id = serie['ejercicio_id']

                            # Convertir peso de forma segura
                            peso_kg = 0.0
                            if serie['peso_kg'] is not None:
                                try:
                                    # Intentar convertir directamente
                                    peso_kg = float(serie['peso_kg'])
                                except (ValueError, TypeError, InvalidOperation):
                                    try:
                                        # Intentar limpiar y convertir
                                        valor_str = str(serie['peso_kg']).replace(',', '.')
                                        valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                                        if valor_limpio:
                                            peso_kg = float(valor_limpio)
                                    except:
                                        peso_kg = 0.0

                            # Convertir repeticiones de forma segura
                            repeticiones = 0
                            if serie['repeticiones'] is not None:
                                try:
                                    repeticiones = int(serie['repeticiones'])
                                except (ValueError, TypeError):
                                    repeticiones = 0

                            # Guardar datos procesados
                            datos_previos.setdefault(ejercicio_id, []).append({
                                'repeticiones': repeticiones,
                                'peso_kg': peso_kg
                            })

                            # Registrar fallos
                            if not serie['completado']:
                                fallos_anteriores.add(ejercicio_id)
                        except Exception as e:
                            logger.error(f"Error al procesar serie {serie.get('id')}: {str(e)}")
                            continue

                    # Calcular fallos por ejercicio
                    for ejercicio_id in set(s['ejercicio_id'] for s in series_rows):
                        series_ejercicio = [s for s in series_rows if s['ejercicio_id'] == ejercicio_id]
                        total = len(series_ejercicio)
                        if total > 0:
                            completadas = sum(1 for s in series_ejercicio if s['completado'])
                            if completadas / total < 0.75:
                                fallos_anteriores.add(ejercicio_id)
            except Exception as e:
                logger.error(f"Error al obtener datos previos: {str(e)}")
                datos_previos = {}
                fallos_anteriores = set()

    # Preparar formularios para cada ejercicio - Manejo seguro
    for asignacion in ejercicios_rutina:
        try:
            # IMPORTANTE: Usar diccionario en lugar de objeto simulado
            ejercicio_dict = {
                'id': asignacion['ej_id'],
                'nombre': asignacion['ej_nombre'],
                'grupo_muscular': asignacion.get('grupo_muscular', 'general'),
                'equipo': asignacion.get('equipo', ''),
                'series_datos': []  # Inicializar lista vacía para series
            }

            plan = None
            adaptado = False
            registro_fallos = 0

            # Obtener plan personalizado de forma segura
            if isinstance(cliente_inicial, Cliente):
                try:
                    plan = PlanPersonalizado.objects.filter(
                        cliente_id=cliente_inicial.id,
                        ejercicio_id=asignacion['ejercicio_id'],
                        rutina_id=rutina_id
                    ).first()
                except Exception as e:
                    logger.error(f"Error al obtener plan personalizado: {str(e)}")
                    plan = None

            # Manejo seguro de valores decimales
            if plan:
                # Convertir repeticiones de forma segura
                reps_plan = 0
                if plan.repeticiones_objetivo is not None:
                    try:
                        reps_plan = int(plan.repeticiones_objetivo)
                    except (ValueError, TypeError):
                        reps_plan = 0

                # Convertir peso de forma segura
                peso_plan = 0.0
                if plan.peso_objetivo is not None:
                    try:
                        peso_plan = float(plan.peso_objetivo)
                    except (ValueError, TypeError, InvalidOperation):
                        try:
                            peso_plan = float(str(plan.peso_objetivo).replace(',', '.'))
                        except:
                            peso_plan = 0.0

                adaptado = True

                # Obtener número de series de forma segura
                try:
                    num_series = int(asignacion['series'])
                except (ValueError, TypeError):
                    num_series = 3  # Valor por defecto

                # Obtener registro de fallos de la sesión
                session_key = f'adaptacion_{cliente_inicial.id}_{rutina_id}'
                if session_key in request.session:
                    registro = request.session[session_key].get(str(asignacion['ejercicio_id']))
                    if registro:
                        registro_fallos = registro.get('fallos_consecutivos', 0)

                # Crear datos de series
                for idx in range(num_series):
                    ejercicio_dict['series_datos'].append({
                        'repeticiones': reps_plan,
                        'peso_kg': peso_plan,
                        'numero': idx + 1,
                        'adaptado': True,
                        'peso_adaptado': True,
                        'fallo_anterior': asignacion['ejercicio_id'] in fallos_anteriores,
                        'fallos_consecutivos': registro_fallos
                    })
            else:
                previas = datos_previos.get(asignacion['ejercicio_id'], [])

                # Convertir repeticiones de forma segura
                reps_plan = 0
                if asignacion['repeticiones'] is not None:
                    try:
                        reps_plan = int(asignacion['repeticiones'])
                    except (ValueError, TypeError):
                        reps_plan = 0

                # Convertir peso de forma segura
                peso_plan = 0.0
                if asignacion['peso_kg'] is not None:
                    try:
                        peso_plan = float(asignacion['peso_kg'])
                    except (ValueError, TypeError, InvalidOperation):
                        try:
                            peso_plan = float(str(asignacion['peso_kg']).replace(',', '.'))
                        except:
                            peso_plan = 0.0

                # Obtener número de series
                num_series = len(previas) if previas else int(asignacion['series'])

                # Crear datos de series
                for idx in range(num_series):
                    # Valores por defecto seguros
                    rep_valor = reps_plan
                    peso_valor = peso_plan

                    # Si hay datos previos, los usamos con manejo seguro
                    if idx < len(previas):
                        rep_valor = previas[idx]['repeticiones']
                        peso_valor = previas[idx]['peso_kg']

                    ejercicio_dict['series_datos'].append({
                        'repeticiones': rep_valor,
                        'peso_kg': peso_valor,
                        'numero': idx + 1,
                        'adaptado': False,
                        'peso_adaptado': False,
                        'fallo_anterior': asignacion['ejercicio_id'] in fallos_anteriores,
                        'fallos_consecutivos': registro_fallos
                    })

            # IMPORTANTE: Datos iniciales para el formulario
            # Estos no se usan directamente en la plantilla, pero son necesarios para la vista
            initial_data = {
                'ejercicio_id': asignacion['ejercicio_id'],
                'series': len(ejercicio_dict['series_datos']),
                'repeticiones': ejercicio_dict['series_datos'][0]['repeticiones'] if ejercicio_dict[
                    'series_datos'] else 0,
                'peso_kg': ejercicio_dict['series_datos'][0]['peso_kg'] if ejercicio_dict['series_datos'] else 0,
                'completado': True
            }

            # Crear formulario con datos iniciales
            form = DetalleEjercicioForm(initial=initial_data, prefix=str(asignacion['ejercicio_id']))
            ejercicios_forms.append((ejercicio_dict, form))
        except Exception as e:
            logger.error(f"Error al preparar formulario para ejercicio {asignacion.get('ej_nombre')}: {str(e)}")
            # Intentamos crear un formulario básico para no romper la página
            try:
                initial_data = {
                    'ejercicio_id': asignacion.get('ejercicio_id', 0),
                    'series': 0,
                    'repeticiones': 0,
                    'peso_kg': 0,
                    'completado': True
                }
                form = DetalleEjercicioForm(initial=initial_data, prefix=str(asignacion.get('ejercicio_id', 0)))

                # IMPORTANTE: Usar diccionario en lugar de objeto simulado
                ejercicio_dict = {
                    'id': asignacion.get('ej_id', 0),
                    'nombre': asignacion.get('ej_nombre', 'Ejercicio sin nombre'),
                    'grupo_muscular': asignacion.get('grupo_muscular', 'general'),
                    'equipo': asignacion.get('equipo', ''),
                    'series_datos': []
                }

                ejercicios_forms.append((ejercicio_dict, form))
            except:
                continue

    # Renderizar plantilla
    return render(request, 'entrenos/empezar_entreno.html', {
        'rutina': rutina,
        'cliente_form': cliente_form,
        'ejercicios_forms': ejercicios_forms,
        'cliente_inicial': cliente_inicial
    })


def adaptar_plan_personalizado_manual(entreno, request, cliente, rutina):
    """
    Versión adaptada de adaptar_plan_personalizado que procesa los datos del formulario
    según el formato de la plantilla actual.

    Args:
        entreno: Objeto EntrenoRealizado
        request: Objeto HttpRequest
        cliente: Objeto Cliente
        rutina: Objeto Rutina
    """
    import logging
    from decimal import Decimal, InvalidOperation
    from django.db import connection

    logger = logging.getLogger(__name__)

    try:
        adaptaciones_positivas = []
        adaptaciones_negativas = []

        # Obtener ejercicios de la rutina con SQL directo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT re.id, re.rutina_id, re.ejercicio_id, re.series, re.repeticiones, re.peso_kg, 
                       e.id as ej_id, e.nombre as ej_nombre
                FROM rutinas_rutinaejercicio re
                JOIN rutinas_ejercicio e ON re.ejercicio_id = e.id
                WHERE re.rutina_id = %s
            """, [rutina.id])
            columns = [col[0] for col in cursor.description]
            ejercicios_rutina = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Obtener series realizadas con SQL directo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sr.id, sr.entreno_id, sr.ejercicio_id, sr.serie_numero, 
                       sr.repeticiones, sr.peso_kg, sr.completado,
                       e.id as ej_id, e.nombre as ej_nombre
                FROM entrenos_serierealizada sr
                JOIN rutinas_ejercicio e ON sr.ejercicio_id = e.id
                WHERE sr.entreno_id = %s
            """, [entreno.id])
            columns = [col[0] for col in cursor.description]
            series_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Agrupar series por ejercicio
        series_por_ejercicio = {}
        for serie in series_rows:
            ejercicio_id = serie['ejercicio_id']
            if ejercicio_id not in series_por_ejercicio:
                series_por_ejercicio[ejercicio_id] = []
            series_por_ejercicio[ejercicio_id].append(serie)

        # Procesar cada ejercicio
        for asignacion in ejercicios_rutina:
            try:
                ejercicio_id = asignacion['ejercicio_id']
                ej_id = asignacion['ej_id']

                # Verificar si hay series para este ejercicio
                if ejercicio_id not in series_por_ejercicio or not series_por_ejercicio[ejercicio_id]:
                    continue

                # Obtener series del ejercicio
                series = series_por_ejercicio[ejercicio_id]

                # Verificar si todas las series están completadas
                completado = all(serie['completado'] for serie in series)

                # Obtener peso y repeticiones (de la primera serie)
                peso_kg = 0.0
                if series[0]['peso_kg'] is not None:
                    try:
                        peso_kg = float(series[0]['peso_kg'])
                    except (ValueError, TypeError, InvalidOperation):
                        try:
                            valor_str = str(series[0]['peso_kg']).replace(',', '.')
                            valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                            if valor_limpio:
                                peso_kg = float(valor_limpio)
                        except:
                            peso_kg = 0.0

                repeticiones = 0
                if series[0]['repeticiones'] is not None:
                    try:
                        repeticiones = int(series[0]['repeticiones'])
                    except (ValueError, TypeError):
                        repeticiones = 0

                # Obtener o crear plan personalizado
                plan, created = PlanPersonalizado.objects.get_or_create(
                    cliente=cliente,
                    rutina=rutina,
                    ejercicio_id=ejercicio_id,
                    defaults={
                        'series': len(series),
                        'repeticiones_objetivo': repeticiones,
                        'peso_objetivo': peso_kg
                    }
                )

                # Procesar adaptaciones según el resultado del entreno
                if completado:
                    # Éxito: aumentar peso
                    peso_anterior = plan.peso_objetivo
                    plan.peso_objetivo = round(float(peso_kg) * 1.05, 1)  # Incremento del 5%
                    plan.save()

                    adaptaciones_positivas.append({
                        'ejercicio': asignacion['ej_nombre'],
                        'peso_anterior': peso_anterior,
                        'peso_nuevo': plan.peso_objetivo
                    })

                    # Actualizar registro de fallos
                    session_key = f'adaptacion_{cliente.id}_{rutina.id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 0}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] = 0

                    request.session.modified = True
                else:
                    # Fallo: disminuir peso si hay fallos consecutivos
                    session_key = f'adaptacion_{cliente.id}_{rutina.id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 1}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] += 1

                    fallos = request.session[session_key][str(ejercicio_id)]['fallos_consecutivos']
                    request.session.modified = True

                    if fallos >= 2:
                        # Dos fallos consecutivos: reducir peso
                        peso_anterior = plan.peso_objetivo
                        plan.peso_objetivo = round(float(peso_kg) * 0.9, 1)  # Reducción del 10%
                        plan.save()

                        adaptaciones_negativas.append({
                            'ejercicio': asignacion['ej_nombre'],
                            'peso_anterior': peso_anterior,
                            'peso_nuevo': plan.peso_objetivo,
                            'fallos_consecutivos': fallos
                        })
            except Exception as e:
                logger.error(f"Error al adaptar plan para ejercicio {asignacion.get('ej_nombre')}: {str(e)}")
                continue

        # Guardar adaptaciones en la sesión para mostrarlas en el resumen
        request.session['adaptaciones_positivas'] = adaptaciones_positivas
        request.session['adaptaciones_negativas'] = adaptaciones_negativas
        request.session.modified = True

    except Exception as e:
        logger.error(f"Error general en adaptar_plan_personalizado_manual: {str(e)}")


def crear_entreno_seguro(entreno, ejercicios_forms, request):
    """
    Versión segura que no usa form.cleaned_data y toma los datos directamente del POST.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        for ejercicio_dict, _ in ejercicios_forms:
            try:
                ejercicio_id = int(ejercicio_dict['id'])

                i = 1
                while True:
                    reps_key = f"{ejercicio_id}_reps_{i}"
                    peso_key = f"{ejercicio_id}_peso_{i}"
                    completado_key = f"{ejercicio_id}_completado_{i}"

                    reps = request.POST.get(reps_key)
                    peso = request.POST.get(peso_key)
                    completado = request.POST.get(completado_key) == "1"

                    if reps is None or peso is None:
                        break

                    if reps.strip() == '' and peso.strip() == '':
                        i += 1
                        continue

                    SerieRealizada.objects.create(
                        entreno=entreno,
                        ejercicio_id=ejercicio_id,
                        serie_numero=i,
                        repeticiones=int(reps),
                        peso_kg=float(peso.replace(',', '.')),
                        completado=completado
                    )
                    i += 1

            except Exception as e:
                logger.error(f"Error al procesar serie para ejercicio {ejercicio_dict.get('nombre')}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error general en crear_entreno_seguro: {str(e)}")


def adaptar_plan_personalizado_seguro(entreno, ejercicios_forms, cliente_id, rutina_id, request):
    """
    Versión segura de adaptar_plan_personalizado que usa solo IDs y no objetos simulados.

    Args:
        entreno: Objeto EntrenoRealizado
        ejercicios_forms: Lista de tuplas (ejercicio_dict, form)
        cliente_id: ID del cliente
        rutina_id: ID de la rutina
        request: Objeto HttpRequest
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        adaptaciones_positivas = []
        adaptaciones_negativas = []

        # Procesar cada ejercicio
        for ejercicio_dict, form in ejercicios_forms:
            if form.is_valid():
                # Obtener datos del formulario
                ejercicio_id = form.cleaned_data.get('ejercicio_id')
                series = form.cleaned_data.get('series', 0)
                repeticiones = form.cleaned_data.get('repeticiones', 0)
                peso_kg = form.cleaned_data.get('peso_kg', 0)
                completado = form.cleaned_data.get('completado', False)

                # Validar que ejercicio_id sea un ID válido
                if not isinstance(ejercicio_id, int) and not (isinstance(ejercicio_id, str) and ejercicio_id.isdigit()):
                    logger.error(
                        f"Error procesando {ejercicio_dict['nombre']}: Field 'id' expected a number but got {type(ejercicio_id)}.")
                    continue

                # Convertir a entero si es necesario
                if isinstance(ejercicio_id, str):
                    ejercicio_id = int(ejercicio_id)

                # Obtener o crear plan personalizado
                plan, created = PlanPersonalizado.objects.get_or_create(
                    cliente_id=cliente_id,
                    rutina_id=rutina_id,
                    ejercicio_id=ejercicio_id,  # Usar ID, no objeto
                    defaults={
                        'series': series,
                        'repeticiones_objetivo': repeticiones,
                        'peso_objetivo': peso_kg
                    }
                )

                # Procesar adaptaciones según el resultado del entreno
                if completado:
                    # Éxito: aumentar peso
                    peso_anterior = plan.peso_objetivo
                    plan.peso_objetivo = round(float(peso_kg) * 1.05, 1)  # Incremento del 5%
                    plan.save()

                    adaptaciones_positivas.append({
                        'ejercicio': ejercicio_dict['nombre'],
                        'peso_anterior': peso_anterior,
                        'peso_nuevo': plan.peso_objetivo
                    })

                    # Actualizar registro de fallos
                    session_key = f'adaptacion_{cliente_id}_{rutina_id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 0}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] = 0

                    request.session.modified = True
                else:
                    # Fallo: disminuir peso si hay fallos consecutivos
                    session_key = f'adaptacion_{cliente_id}_{rutina_id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 1}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] += 1

                    fallos = request.session[session_key][str(ejercicio_id)]['fallos_consecutivos']
                    request.session.modified = True

                    if fallos >= 2:
                        # Dos fallos consecutivos: reducir peso
                        peso_anterior = plan.peso_objetivo
                        plan.peso_objetivo = round(float(peso_kg) * 0.9, 1)  # Reducción del 10%
                        plan.save()

                        adaptaciones_negativas.append({
                            'ejercicio': ejercicio_dict['nombre'],
                            'peso_anterior': peso_anterior,
                            'peso_nuevo': plan.peso_objetivo,
                            'fallos_consecutivos': fallos
                        })

        # Guardar adaptaciones en la sesión para mostrarlas en el resumen
        request.session['adaptaciones_positivas'] = adaptaciones_positivas
        request.session['adaptaciones_negativas'] = adaptaciones_negativas
        request.session.modified = True

    except Exception as e:
        logger.error(f"Error general en adaptar_plan_personalizado_seguro: {str(e)}")


def crear_entreno_seguro(entreno, ejercicios_forms, request):
    """
    Versión segura de crear_entreno que usa solo IDs y no objetos simulados.

    Args:
        entreno: Objeto EntrenoRealizado
        ejercicios_forms: Lista de tuplas (ejercicio_dict, form)
        request: Objeto HttpRequest
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Procesar cada ejercicio
        for ejercicio_dict, form in ejercicios_forms:
            if form.is_valid():
                # Obtener datos del formulario
                ejercicio_id = form.cleaned_data.get('ejercicio_id')
                series = form.cleaned_data.get('series', 0)
                repeticiones = form.cleaned_data.get('repeticiones', 0)
                peso_kg = form.cleaned_data.get('peso_kg', 0)
                completado = form.cleaned_data.get('completado', False)

                # Validar que ejercicio_id sea un ID válido
                if not isinstance(ejercicio_id, int) and not (isinstance(ejercicio_id, str) and ejercicio_id.isdigit()):
                    logger.error(
                        f"Error procesando {ejercicio_dict['nombre']}: Field 'id' expected a number but got {type(ejercicio_id)}.")
                    continue

                # Convertir a entero si es necesario
                if isinstance(ejercicio_id, str):
                    ejercicio_id = int(ejercicio_id)

                # Crear series realizadas
                for i in range(1, series + 1):
                    try:
                        # Crear serie con ID de ejercicio, no con objeto
                        SerieRealizada.objects.create(
                            entreno=entreno,
                            ejercicio_id=ejercicio_id,  # Usar ID, no objeto
                            serie_numero=i,
                            repeticiones=repeticiones,
                            peso_kg=peso_kg,
                            completado=completado
                        )
                    except Exception as e:
                        logger.error(f"Error al crear serie {i} para ejercicio {ejercicio_dict['nombre']}: {str(e)}")
            else:
                logger.error(f"Formulario inválido para ejercicio {ejercicio_dict['nombre']}: {form.errors}")
    except Exception as e:
        logger.error(f"Error general en crear_entreno_seguro: {str(e)}")


def adaptar_plan_personalizado_seguro(entreno, ejercicios_forms, cliente_id, rutina_id, request):
    """
    Versión segura de adaptar_plan_personalizado que usa solo IDs y no objetos simulados.

    Args:
        entreno: Objeto EntrenoRealizado
        ejercicios_forms: Lista de tuplas (ejercicio_dict, form)
        cliente_id: ID del cliente
        rutina_id: ID de la rutina
        request: Objeto HttpRequest
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        adaptaciones_positivas = []
        adaptaciones_negativas = []

        # Procesar cada ejercicio
        for ejercicio_dict, form in ejercicios_forms:
            if form.is_valid():
                # Obtener datos del formulario
                ejercicio_id = form.cleaned_data.get('ejercicio_id')
                series = form.cleaned_data.get('series', 0)
                repeticiones = form.cleaned_data.get('repeticiones', 0)
                peso_kg = form.cleaned_data.get('peso_kg', 0)
                completado = form.cleaned_data.get('completado', False)

                # Validar que ejercicio_id sea un ID válido
                if not isinstance(ejercicio_id, int) and not (isinstance(ejercicio_id, str) and ejercicio_id.isdigit()):
                    logger.error(
                        f"Error procesando {ejercicio_dict['nombre']}: Field 'id' expected a number but got {type(ejercicio_id)}.")
                    continue

                # Convertir a entero si es necesario
                if isinstance(ejercicio_id, str):
                    ejercicio_id = int(ejercicio_id)

                # Obtener o crear plan personalizado
                plan, created = PlanPersonalizado.objects.get_or_create(
                    cliente_id=cliente_id,
                    rutina_id=rutina_id,
                    ejercicio_id=ejercicio_id,  # Usar ID, no objeto
                    defaults={
                        'series': series,
                        'repeticiones_objetivo': repeticiones,
                        'peso_objetivo': peso_kg
                    }
                )

                # Procesar adaptaciones según el resultado del entreno
                if completado:
                    # Éxito: aumentar peso
                    peso_anterior = plan.peso_objetivo
                    plan.peso_objetivo = round(float(peso_kg) * 1.05, 1)  # Incremento del 5%
                    plan.save()

                    adaptaciones_positivas.append({
                        'ejercicio': ejercicio_dict['nombre'],
                        'peso_anterior': peso_anterior,
                        'peso_nuevo': plan.peso_objetivo
                    })

                    # Actualizar registro de fallos
                    session_key = f'adaptacion_{cliente_id}_{rutina_id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 0}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] = 0

                    request.session.modified = True
                else:
                    # Fallo: disminuir peso si hay fallos consecutivos
                    session_key = f'adaptacion_{cliente_id}_{rutina_id}'
                    if session_key not in request.session:
                        request.session[session_key] = {}

                    if str(ejercicio_id) not in request.session[session_key]:
                        request.session[session_key][str(ejercicio_id)] = {'fallos_consecutivos': 1}
                    else:
                        request.session[session_key][str(ejercicio_id)]['fallos_consecutivos'] += 1

                    fallos = request.session[session_key][str(ejercicio_id)]['fallos_consecutivos']
                    request.session.modified = True

                    if fallos >= 2:
                        # Dos fallos consecutivos: reducir peso
                        peso_anterior = plan.peso_objetivo
                        plan.peso_objetivo = round(float(peso_kg) * 0.9, 1)  # Reducción del 10%
                        plan.save()

                        adaptaciones_negativas.append({
                            'ejercicio': ejercicio_dict['nombre'],
                            'peso_anterior': peso_anterior,
                            'peso_nuevo': plan.peso_objetivo,
                            'fallos_consecutivos': fallos
                        })

        # Guardar adaptaciones en la sesión para mostrarlas en el resumen
        request.session['adaptaciones_positivas'] = adaptaciones_positivas
        request.session['adaptaciones_negativas'] = adaptaciones_negativas
        request.session.modified = True

    except Exception as e:
        logger.error(f"Error general en adaptar_plan_personalizado_seguro: {str(e)}")


def hacer_entreno(request):
    """
    Muestra una lista de clientes para seleccionar al iniciar un entrenamiento.

    Args:
        request: Objeto HttpRequest

    Returns:
        HttpResponse con la plantilla renderizada
    """
    clientes = Cliente.objects.select_related('programa', 'rutina_actual').all()
    return render(request, 'entrenos/hacer_entreno.html', {
        'clientes': clientes
    })


def eliminar_entreno(request, pk):
    """
    Elimina un entrenamiento específico.

    Args:
        request: Objeto HttpRequest
        pk: ID del entrenamiento a eliminar

    Returns:
        HttpResponseRedirect a la página de historial de entrenamientos
    """
    if request.method == 'POST':
        try:
            entreno = get_object_or_404(EntrenoRealizado, pk=pk)
            entreno.delete()
            messages.success(request, "✅ Entrenamiento eliminado con éxito.")
        except Exception as e:
            messages.error(request, f"⚠️ Error al eliminar entrenamiento: {str(e)}")
    return redirect('historial_entrenos')


def mostrar_entreno_anterior(request, cliente_id, rutina_id):
    """
    Muestra los detalles de un entrenamiento anterior con manejo seguro de valores decimales.
    Versión final robusta que usa SQL directo para evitar errores de conversión decimal
    y diccionarios simples en lugar de objetos simulados.

    Args:
        request: Objeto HttpRequest
        cliente_id: ID del cliente
        rutina_id: ID de la rutina

    Returns:
        HttpResponse con la plantilla renderizada
    """
    from decimal import Decimal, InvalidOperation
    import logging
    from django.db import connection
    from django.utils.dateformat import DateFormat
    from django.db.models import Sum
    import json

    # Configurar logging para depuración
    logger = logging.getLogger(__name__)

    # Obtenemos el cliente y la rutina por ID de forma segura
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        rutina = get_object_or_404(Rutina, id=rutina_id)
    except Exception as e:
        logger.error(f"Error al obtener cliente o rutina: {str(e)}")
        messages.error(request, "Error al cargar los datos. Por favor, inténtalo de nuevo.")
        return redirect('home')

    # Último entreno realizado - Usando SQL directo para evitar errores de conversión
    entreno_anterior = None
    series_procesadas = []

    try:
        # Obtener último entreno con SQL directo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, fecha
                FROM entrenos_entrenorealizado
                WHERE cliente_id = %s AND rutina_id = %s
                ORDER BY fecha DESC, id DESC
                LIMIT 1
            """, [cliente_id, rutina_id])
            entreno_row = cursor.fetchone()

        if entreno_row:
            entreno_id = entreno_row[0]
            fecha = entreno_row[1]

            # IMPORTANTE: Usar diccionario en lugar de objeto simulado
            entreno_anterior = {
                'id': entreno_id,
                'fecha': fecha,
                'cliente_id': cliente_id,
                'rutina_id': rutina_id,
                'cliente_nombre': cliente.nombre if hasattr(cliente, 'nombre') else str(cliente),
                'rutina_nombre': rutina.nombre if hasattr(rutina, 'nombre') else str(rutina)
            }

            # Obtener series con SQL directo
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT sr.id, sr.entreno_id, sr.ejercicio_id, sr.serie_numero, 
                           sr.repeticiones, sr.peso_kg, sr.completado,
                           e.id as ej_id, e.nombre as ej_nombre
                    FROM entrenos_serierealizada sr
                    JOIN rutinas_ejercicio e ON sr.ejercicio_id = e.id
                    WHERE sr.entreno_id = %s
                """, [entreno_id])
                columns = [col[0] for col in cursor.description]
                series_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Procesar series de forma segura
            for serie in series_rows:
                try:
                    # IMPORTANTE: Usar diccionario en lugar de objeto simulado para ejercicio
                    ejercicio_dict = {
                        'id': serie['ej_id'],
                        'nombre': serie['ej_nombre']
                    }

                    # Convertir peso de forma segura
                    peso_kg = 0.0
                    if serie['peso_kg'] is not None:
                        try:
                            # Intentar convertir directamente
                            peso_kg = float(serie['peso_kg'])
                        except (ValueError, TypeError, InvalidOperation):
                            try:
                                # Intentar limpiar y convertir
                                valor_str = str(serie['peso_kg']).replace(',', '.')
                                valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                                if valor_limpio:
                                    peso_kg = float(valor_limpio)
                            except:
                                peso_kg = 0.0

                    # Convertir repeticiones de forma segura
                    repeticiones = 0
                    if serie['repeticiones'] is not None:
                        try:
                            repeticiones = int(serie['repeticiones'])
                        except (ValueError, TypeError):
                            repeticiones = 0

                    # IMPORTANTE: Crear diccionario en lugar de objeto simulado para serie
                    serie_procesada = {
                        'id': serie['id'],
                        'serie_numero': serie['serie_numero'],
                        'repeticiones': repeticiones,
                        'peso_kg': peso_kg,
                        'completado': serie['completado'],
                        'ejercicio': ejercicio_dict  # Usar diccionario, no objeto simulado
                    }
                    series_procesadas.append(serie_procesada)
                except Exception as e:
                    logger.error(f"Error al procesar serie {serie.get('id')}: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Error al obtener entreno anterior: {str(e)}")
        entreno_anterior = None
        series_procesadas = []

    # Plan personalizado o rutina original - Usando SQL directo
    ejercicios_planificados = []

    try:
        # Obtener ejercicios de la rutina con SQL directo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT re.id, re.rutina_id, re.ejercicio_id, re.series, re.repeticiones, re.peso_kg, 
                       e.id as ej_id, e.nombre as ej_nombre
                FROM rutinas_rutinaejercicio re
                JOIN rutinas_ejercicio e ON re.ejercicio_id = e.id
                WHERE re.rutina_id = %s
            """, [rutina_id])
            columns = [col[0] for col in cursor.description]
            ejercicios_rutina = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Obtener planes personalizados con SQL directo
        planes_personalizados = {}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, cliente_id, ejercicio_id, rutina_id, repeticiones_objetivo, peso_objetivo
                FROM entrenos_planpersonalizado
                WHERE cliente_id = %s AND rutina_id = %s
            """, [cliente_id, rutina_id])
            columns = [col[0] for col in cursor.description]
            planes_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Indexar planes por ejercicio_id para acceso rápido
            for plan in planes_rows:
                planes_personalizados[plan['ejercicio_id']] = plan

        # Procesar cada ejercicio de la rutina
        for asignacion in ejercicios_rutina:
            try:
                ejercicio_id = asignacion['ejercicio_id']

                # Obtener plan personalizado si existe
                plan = planes_personalizados.get(ejercicio_id)

                # Manejo seguro de valores decimales
                peso_base = 0.0
                if asignacion['peso_kg'] is not None:
                    try:
                        peso_base = float(asignacion['peso_kg'])
                    except (ValueError, TypeError, InvalidOperation):
                        try:
                            valor_str = str(asignacion['peso_kg']).replace(',', '.')
                            valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                            if valor_limpio:
                                peso_base = float(valor_limpio)
                        except:
                            peso_base = 0.0

                peso_adaptado = False
                peso_objetivo = peso_base

                if plan and plan['peso_objetivo'] is not None:
                    try:
                        plan_peso_objetivo = float(plan['peso_objetivo'])
                        if abs(plan_peso_objetivo - peso_base) > 0.001:  # Comparación con tolerancia para decimales
                            peso_objetivo = plan_peso_objetivo
                            peso_adaptado = True
                    except (ValueError, TypeError, InvalidOperation):
                        try:
                            valor_str = str(plan['peso_objetivo']).replace(',', '.')
                            valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                            if valor_limpio:
                                plan_peso_objetivo = float(valor_limpio)
                                if abs(plan_peso_objetivo - peso_base) > 0.001:
                                    peso_objetivo = plan_peso_objetivo
                                    peso_adaptado = True
                        except:
                            peso_objetivo = peso_base

                ejercicios_planificados.append({
                    'nombre': asignacion['ej_nombre'],
                    'series': asignacion['series'],
                    'repeticiones': asignacion['repeticiones'],
                    'peso_kg': peso_objetivo,
                    'peso_adaptado': peso_adaptado,
                    'peso_base': peso_base
                })
            except Exception as e:
                logger.error(f"Error al procesar ejercicio {asignacion.get('ej_nombre')}: {str(e)}")
                # Intentamos añadir información básica incluso si hay error
                try:
                    ejercicios_planificados.append({
                        'nombre': asignacion.get('ej_nombre', 'Ejercicio sin nombre'),
                        'series': asignacion.get('series', 0),
                        'repeticiones': asignacion.get('repeticiones', 0),
                        'peso_kg': 0.0,
                        'peso_adaptado': False,
                        'peso_base': 0.0
                    })
                except:
                    pass
    except Exception as e:
        logger.error(f"Error al procesar ejercicios planificados: {str(e)}")
        ejercicios_planificados = []
    # Cargar último logro

    ultimo_logro = LogroDesbloqueado.objects.filter(cliente=cliente).order_by('-fecha').first()

    # Estado emocional más reciente

    estado_emocional = EstadoEmocional.objects.filter(cliente=cliente).order_by('-fecha').first()

    # Progreso semanal simulado (reemplazar por datos reales si los tienes)
    # Obtener últimos 7 días de entrenamientos reales del cliente
    # ✅ Gráfica real con progreso de volumen total por día
    try:
        ultimos_entrenos = (
            EntrenoRealizado.objects.filter(cliente=cliente)
            .order_by('-fecha')
            .values('fecha')
            .annotate(volumen_total=Sum('series__peso_kg'))
            [:7][::-1]
        )
        progreso_fechas = [DateFormat(e['fecha']).format("d M") for e in ultimos_entrenos]
        progreso_valores = [float(e['volumen_total'] or 0.0) for e in ultimos_entrenos]
    except Exception as e:
        logger.error(f"Error al generar datos de gráfico: {str(e)}")
        progreso_fechas = []
        progreso_valores = []
    # Añadir información de depuración al contexto
    # --- Comparativa de progreso respecto al entreno anterior ---
    volumen_actual = 0
    volumen_anterior = 0
    dias_entre_entrenos = None
    diferencia_porcentual = 0
    mensaje_comparativa = ""

    try:
        entrenos = (
            EntrenoRealizado.objects
            .filter(cliente=cliente, rutina=rutina)
            .annotate(total_series=Count('series'))
            .filter(total_series__gt=0)
            .order_by('-id')

        )

        if entrenos.count() >= 2:
            actual = entrenos[0]
            anterior = entrenos[1]
            print("▶️ ENTRENOS DETECTADOS:")
            print(f"   Actual ID: {actual.id}, Fecha: {actual.fecha}")
            print(f"   Anterior ID: {anterior.id}, Fecha: {anterior.fecha}")
            series_actual = SerieRealizada.objects.filter(entreno=actual)
            series_anterior = SerieRealizada.objects.filter(entreno=anterior)

            print("🔍 SERIES ACTUAL:")
            for s in series_actual:
                print(f"{s.ejercicio.nombre} - {s.peso_kg} kg")

            print("🔍 SERIES ANTERIOR:")
            for s in series_anterior:
                print(f"{s.ejercicio.nombre} - {s.peso_kg} kg")

            dias_entre_entrenos = (actual.fecha - anterior.fecha).days

            volumen_actual = SerieRealizada.objects.filter(entreno=actual).aggregate(
                total=Sum('peso_kg'))['total'] or 0
            volumen_anterior = SerieRealizada.objects.filter(entreno=anterior).aggregate(
                total=Sum('peso_kg'))['total'] or 0

            if volumen_anterior > 0:
                diferencia_porcentual = round(((volumen_actual - volumen_anterior) / volumen_anterior) * 100, 1)
                if diferencia_porcentual > 0:
                    mensaje_comparativa = f"Subiste el volumen total un {diferencia_porcentual} % 💪"
                elif diferencia_porcentual < 0:
                    mensaje_comparativa = f"Bajaste el volumen total un {abs(diferencia_porcentual)} % 💤"
                else:
                    mensaje_comparativa = "Mantuviste el mismo volumen que el entreno anterior. 🎯"
        else:
            mensaje_comparativa = "Aún no hay suficientes datos para comparar el volumen."
    except Exception as e:
        logger.error(f"Error al calcular la comparativa de volumen: {str(e)}")
        mensaje_comparativa = "No se pudo calcular la comparativa de volumen."

    # --- Comparativa por ejercicio: mejora o estancamiento ---
    mejor_ejercicio = None
    mejora_kg = 0
    ejercicio_estancado = None

    try:
        if entrenos.count() >= 2:
            actual = entrenos[0]
            anterior = entrenos[1]

            max_mejora = -999
            max_bajada = 0
            ejercicios_actual = (
                SerieRealizada.objects
                .filter(entreno=actual)
                .values('ejercicio__id', 'ejercicio__nombre')
                .annotate(peso_prom=Avg('peso_kg'))
            )

            ejercicios_anterior = {
                e['ejercicio__id']: e for e in SerieRealizada.objects
                .filter(entreno=anterior)
                .values('ejercicio__id', 'ejercicio__nombre')
                .annotate(peso_prom=Avg('peso_kg'))
            }

            max_mejora = -999
            max_bajada = 0

            for e in ejercicios_actual:
                eid = e['ejercicio__id']
                nombre = e['ejercicio__nombre']
                peso_actual = e['peso_prom'] or 0
                anterior_data = ejercicios_anterior.get(eid)
                peso_anterior = anterior_data['peso_prom'] if anterior_data else 0

                diferencia = round(peso_actual - peso_anterior, 1)

                if diferencia > max_mejora:
                    max_mejora = diferencia
                    mejor_ejercicio = nombre
                    mejora_kg = diferencia
                    peso_anterior_ej = peso_anterior
                    peso_actual_ej = peso_actual

                if diferencia <= 0 and abs(diferencia) > max_bajada:
                    max_bajada = abs(diferencia)
                    ejercicio_estancado = nombre

            mejora_kg = round(mejora_kg, 1)
        else:
            logger.info(f"✅ Comparación realizada: mejor ejercicio = {mejor_ejercicio}, mejora = {mejora_kg} kg")


    except Exception as e:
        logger.error(f"Error al calcular mejora por ejercicio: {str(e)}")

    # --- Logros recientes del cliente ---
    logros_recientes = []
    try:
        logros_recientes = LogroDesbloqueado.objects.filter(
            cliente=cliente
        ).order_by('-fecha')[:3]
    except Exception as e:
        logger.error(f"Error al obtener logros recientes: {str(e)}")
    volumen_actual = round(volumen_actual, 1)
    volumen_anterior = round(volumen_anterior, 1)
    mejora_kg = round(mejora_kg, 1)
    context = {
        'cliente': cliente,
        'rutina': rutina,
        'mejor_ejercicio': mejor_ejercicio,
        'logros_recientes': logros_recientes,
        'mejora_kg': mejora_kg,
        'ejercicio_estancado': ejercicio_estancado,
        'volumen_actual': volumen_actual,
        'volumen_anterior': volumen_anterior,
        'mensaje_comparativa': mensaje_comparativa,
        'peso_anterior_ej': round(peso_anterior_ej, 1) if 'peso_anterior_ej' in locals() else None,
        'peso_actual_ej': round(peso_actual_ej, 1) if 'peso_actual_ej' in locals() else None,
        'ultimo_logro': ultimo_logro,
        'estado_emocional': estado_emocional,
        'progreso_fechas': json.dumps(progreso_fechas),
        'progreso_valores': json.dumps(progreso_valores),
        'entreno': entreno_anterior,
        'series_procesadas': series_procesadas,  # ¡Clave para la plantilla corregida!
        'plan': ejercicios_planificados,
        'debug_info': {
            'tiene_entreno': entreno_anterior is not None,
            'num_series_procesadas': len(series_procesadas),
            'num_ejercicios': len(ejercicios_planificados),
        },
        'estado_joi': 'normal',  # también puedes probar con 'feliz', 'triste', 'glitch'
        'frase_forma_joi': "¿Listo para continuar lo que empezaste ayer?",
        'frase_extra_joi': "",
        'frase_recaida': "",
    }

    return render(request, 'entrenos/entreno_anterior.html', context)


import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateformat import DateFormat

from clientes.models import Cliente
from .models import EntrenoRealizado, PlanPersonalizado, SerieRealizada
from rutinas.models import Rutina, RutinaEjercicio
from .models import EjercicioBase

logger = logging.getLogger(__name__)


# Clase para codificar Decimal y datetime en JSON (Mantén solo una vez)
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# entrenos/views.py

# Asegúrate de tener estos imports al principio de tu archivo
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, fields
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateformat import DateFormat

from clientes.models import Cliente
from .models import EntrenoRealizado, SerieRealizada, EjercicioBase
from rutinas.models import Rutina

logger = logging.getLogger(__name__)


# Clase para codificar datos complejos a JSON (si no la tienes ya)
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def resumen_entreno(request, pk):
    """
    Vista completamente renovada para mostrar un resumen detallado y motivador
    del entrenamiento realizado.
    """
    try:
        # --- 1. OBTENER DATOS BÁSICOS ---
        entreno_actual = get_object_or_404(
            EntrenoRealizado.objects.select_related('cliente', 'rutina'),
            pk=pk
        )
        cliente = entreno_actual.cliente

        # --- 2. DETALLES DEL ENTRENAMIENTO ACTUAL ---
        series_actuales = SerieRealizada.objects.filter(entreno=entreno_actual).select_related('ejercicio')

        # Agrupar series por ejercicio para un resumen claro
        ejercicios_realizados = defaultdict(list)
        for serie in series_actuales:
            ejercicios_realizados[serie.ejercicio.nombre].append({
                'reps': serie.repeticiones,
                'peso': round(serie.peso_kg, 1)
            })

        # Calcular estadísticas clave del entreno
        stats_actual = series_actuales.aggregate(
            total_series=Count('id'),
            series_completadas=Count('id', filter=F('completado')),
            volumen_total=Sum(ExpressionWrapper(F('repeticiones') * F('peso_kg'), output_field=fields.DecimalField())),
            peso_maximo=Max('peso_kg')
        )

        entreno_perfecto = (stats_actual['total_series'] > 0 and
                            stats_actual['total_series'] == stats_actual['series_completadas'])

        # --- 3. COMPARATIVA CON EL ENTRENAMIENTO ANTERIOR (de la misma rutina) ---
        entreno_anterior = EntrenoRealizado.objects.filter(
            cliente=cliente,
            rutina=entreno_actual.rutina,
            pk__lt=entreno_actual.pk  # Entrenos anteriores
        ).order_by('-fecha', '-id').first()

        comparativa = {'disponible': False}
        if entreno_anterior:
            stats_anterior = SerieRealizada.objects.filter(entreno=entreno_anterior).aggregate(
                volumen_total=Sum(
                    ExpressionWrapper(F('repeticiones') * F('peso_kg'), output_field=fields.DecimalField()))
            )

            vol_actual = stats_actual.get('volumen_total') or 0
            vol_anterior = stats_anterior.get('volumen_total') or 0

            if vol_anterior > 0:
                diferencia_vol = vol_actual - vol_anterior
                porcentaje_vol = round((diferencia_vol / vol_anterior) * 100, 1)
                comparativa = {
                    'disponible': True,
                    'volumen_actual': round(vol_actual, 1),
                    'volumen_anterior': round(vol_anterior, 1),
                    'diferencia_porcentual': porcentaje_vol
                }

        # --- 4. LOGROS Y MEDALLAS ---
        # Lógica simple de ejemplo, puedes expandirla mucho más
        medallas = []
        if entreno_perfecto:
            medallas.append(
                {'icono': '🎯', 'nombre': 'Precisión Absoluta', 'desc': 'Completaste todas las series al 100%.'})

        if stats_actual.get('peso_maximo', 0) > 100:
            medallas.append(
                {'icono': '🏋️', 'nombre': 'Club de los 100kg', 'desc': 'Levantaste más de 100kg en un ejercicio.'})

        if comparativa.get('diferencia_porcentual', 0) > 10:
            medallas.append({'icono': '🚀', 'nombre': 'Salto Cuántico', 'desc': 'Aumentaste tu volumen más de un 10%.'})

        # --- 5. GRÁFICO DE PROGRESO DE VOLUMEN ---
        ultimos_entrenos = EntrenoRealizado.objects.filter(
            cliente=cliente,
            rutina=entreno_actual.rutina
        ).order_by('fecha', 'id').values('fecha').annotate(
            volumen=Sum(
                ExpressionWrapper(F('series__repeticiones') * F('series__peso_kg'), output_field=fields.DecimalField()))
        )

        progreso_chart_data = {
            "labels": [DateFormat(e['fecha']).format("d M") for e in ultimos_entrenos],
            "data": [float(e['volumen'] or 0) for e in ultimos_entrenos]
        }

        # --- 6. CONTEXTO PARA LA PLANTILLA ---
        context = {
            'entreno': entreno_actual,
            'cliente': cliente,
            'ejercicios_realizados': dict(ejercicios_realizados),
            'stats': {
                'volumen_total': round(stats_actual.get('volumen_total') or 0, 1),
                'peso_maximo': round(stats_actual.get('peso_maximo') or 0, 1),
                'total_series': stats_actual.get('total_series', 0),
                'series_completadas': stats_actual.get('series_completadas', 0),
                'duracion': entreno_actual.duracion_minutos,
            },
            'entreno_perfecto': entreno_perfecto,
            'comparativa': comparativa,
            'medallas': medallas,
            'progreso_chart_data_json': json.dumps(progreso_chart_data, cls=CustomJSONEncoder)
        }

        return render(request, 'entrenos/resumen_entreno.html', context)

    except Exception as e:
        logger.error(f"Error al generar el resumen del entreno {pk}: {e}")
        messages.error(request, "Ocurrió un error al generar el resumen. Por favor, intenta de nuevo.")
        return redirect('entrenos:historial_entrenos')


# Archivo: entrenos/views_liftin_adicionales.py - VISTAS ADICIONALES PARA LIFTIN

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
import json
import csv
from datetime import datetime, timedelta

from .models import EntrenoRealizado, EjercicioLiftinDetallado, DatosLiftinDetallados
from .forms import (
    ImportarLiftinCompletoForm,
    ImportarLiftinBasicoForm,
    BuscarEntrenamientosLiftinForm,
    ExportarDatosForm,
    EjercicioLiftinFormSet
)
from clientes.models import Cliente


# ============================================================================
# VISTAS PRINCIPALES DE IMPORTACIÓN
# ============================================================================

@login_required
def importar_liftin_completo(request):
    """
    Vista definitiva basada en la estructura real de la base de datos
    """
    try:
        # ============================================================================
        # MÉTODO GET - MOSTRAR FORMULARIO
        # ============================================================================
        from datetime import date

        if request.method == 'GET':
            logger.info("Mostrando formulario de importación Liftin")

            try:
                from entrenos.models import Cliente
                from rutinas.models import Rutina  # Rutina está en app rutinas, no entrenos

                clientes = Cliente.objects.all().order_by('nombre')
                rutinas = Rutina.objects.all().order_by('nombre')

                context = {
                    'clientes': clientes,
                    'rutinas': rutinas,
                    'hoy': date.today(),  # ✅ Esta línea permite que el campo <input type="date"> funcione correctamente
                }

                return render(request, 'entrenos/importar_liftin_completo.html', context)

            except Exception as e:
                logger.error(f"Error al obtener datos para formulario: {str(e)}")
                messages.error(request, f"Error al cargar el formulario: {str(e)}")
                return redirect('entrenos:dashboard_liftin')
        # ============================================================================
        # MÉTODO POST - PROCESAR FORMULARIO
        # ============================================================================
        elif request.method == 'POST':
            logger.info("Procesando formulario de importación Liftin")

            try:
                # ============================================================================
                # VALIDAR DATOS ESENCIALES
                # ============================================================================
                cliente_id = request.POST.get('cliente')
                from datetime import datetime

                fecha_str = request.POST.get('fecha')
                try:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    messages.error(request, "Fecha inválida")
                    return redirect('entrenos:importar_liftin_completo')

                rutina_id = request.POST.get('rutina')

                if not cliente_id:
                    messages.error(request, "Debe seleccionar un cliente")
                    return redirect('entrenos:importar_liftin_completo')

                if not fecha:
                    messages.error(request, "Debe proporcionar una fecha")
                    return redirect('entrenos:importar_liftin_completo')

                # ============================================================================
                # OBTENER CLIENTE
                # ============================================================================
                from entrenos.models import Cliente, EntrenoRealizado
                from rutinas.models import Rutina

                try:
                    cliente = Cliente.objects.get(id=cliente_id)
                    logger.info(f"Cliente encontrado: {cliente.nombre}")
                except Cliente.DoesNotExist:
                    messages.error(request, "Cliente seleccionado no válido")
                    return redirect('entrenos:importar_liftin_completo')

                # ============================================================================
                # MANEJAR RUTINA OBLIGATORIA - USAR ESTRUCTURA REAL
                # ============================================================================
                rutina = None

                if rutina_id:
                    # Si se seleccionó una rutina, usarla
                    try:
                        rutina = Rutina.objects.get(id=rutina_id)
                        logger.info(f"Rutina seleccionada: {rutina.nombre}")
                    except Rutina.DoesNotExist:
                        logger.warning(f"Rutina con ID {rutina_id} no existe")
                        rutina = None

                if not rutina:
                    # Si no hay rutina seleccionada, usar la primera disponible (ID=1)
                    try:
                        rutina = Rutina.objects.get(id=1)  # "Dia1 - torso" que existe en la DB
                        logger.info(f"Usando rutina por defecto: {rutina.nombre}")
                    except Rutina.DoesNotExist:
                        # Si no existe ID=1, usar la primera disponible
                        rutina = Rutina.objects.first()
                        if rutina:
                            logger.info(f"Usando primera rutina disponible: {rutina.nombre}")
                        else:
                            messages.error(request, "No hay rutinas disponibles en el sistema")
                            return redirect('entrenos:importar_liftin_completo')

                # ============================================================================
                # PROCESAR EJERCICIOS
                # ============================================================================
                ejercicios_texto = []

                for i in range(1, 9):  # 8 ejercicios
                    nombre = request.POST.get(f'ejercicio_{i}_nombre', '').strip()

                    if nombre:
                        estado = request.POST.get(f'ejercicio_{i}_estado', '')
                        peso = request.POST.get(f'ejercicio_{i}_peso', '').strip()
                        series = request.POST.get(f'ejercicio_{i}_series', '').strip()

                        # Formatear ejercicio
                        estado_simbolo = ''
                        if estado == 'completado':
                            estado_simbolo = '✓ '
                        elif estado == 'fallado':
                            estado_simbolo = '✗ '
                        elif estado == 'nuevo':
                            estado_simbolo = 'N '

                        linea = f"{estado_simbolo}{nombre}"
                        if peso:
                            linea += f": {peso}"
                        if series:
                            linea += f", {series}"

                        ejercicios_texto.append(linea)

                # ============================================================================
                # PREPARAR NOTAS COMPLETAS
                # ============================================================================
                notas_generales = request.POST.get('notas', '').strip()
                texto_completo = []

                if notas_generales:
                    texto_completo.append(notas_generales)

                if ejercicios_texto:
                    texto_completo.append("\\n\\nEjercicios Detallados:")
                    texto_completo.extend(ejercicios_texto)

                notas_liftin_completas = "\\n".join(texto_completo)

                # ============================================================================
                # PREPARAR DATOS DEL ENTRENAMIENTO - ESTRUCTURA REAL
                # ============================================================================

                # Datos básicos obligatorios según estructura real
                datos_entrenamiento = {
                    'cliente': cliente,
                    'rutina': rutina,  # ✅ OBLIGATORIO según DB
                    'fecha': fecha,
                    'fuente_datos': 'liftin',
                    'procesado_gamificacion': False,  # ✅ Campo obligatorio según DB
                    'notas_liftin': notas_liftin_completas,  # ✅ Campo correcto para notas
                }

                # Campos opcionales según estructura real
                hora_inicio = request.POST.get('hora_inicio')
                if hora_inicio:
                    datos_entrenamiento['hora_inicio'] = hora_inicio

                duracion_minutos = request.POST.get('duracion_minutos')
                if duracion_minutos:
                    try:
                        datos_entrenamiento['duracion_minutos'] = int(duracion_minutos)
                    except ValueError:
                        pass

                calorias_quemadas = request.POST.get('calorias_quemadas')
                if calorias_quemadas:
                    try:
                        datos_entrenamiento['calorias_quemadas'] = int(calorias_quemadas)
                    except ValueError:
                        pass

                volumen_total_kg = request.POST.get('volumen_total_kg')
                if volumen_total_kg:
                    try:
                        datos_entrenamiento['volumen_total_kg'] = float(volumen_total_kg)
                    except ValueError:
                        pass

                # Campos adicionales específicos de Liftin según estructura real
                if ejercicios_texto:
                    datos_entrenamiento['numero_ejercicios'] = len(ejercicios_texto)

                # ============================================================================
                # CREAR ENTRENAMIENTO
                # ============================================================================
                logger.info(f"Creando entrenamiento con datos: {datos_entrenamiento}")
                entrenamiento = EntrenoRealizado.objects.create(**datos_entrenamiento)
                logger.info(f"Entrenamiento creado exitosamente con ID: {entrenamiento.id}")

                # ============================================================================
                # ACTIVAR LOGROS (SI EXISTE EL SISTEMA)
                # ============================================================================
                try:
                    # Intentar activar logros si el sistema existe
                    activar_logros_liftin(cliente, entrenamiento)
                    logger.info("Logros activados correctamente")
                except Exception as e:
                    logger.warning(f"No se pudieron activar logros: {str(e)}")

                # ============================================================================
                # ÉXITO - REDIRECCIONAR
                # ============================================================================
                mensaje_exito = f"Entrenamiento de Liftin importado exitosamente para {cliente.nombre}"
                if rutina:
                    mensaje_exito += f" (Rutina: {rutina.nombre})"
                if ejercicios_texto:
                    mensaje_exito += f" con {len(ejercicios_texto)} ejercicios"

                messages.success(request, mensaje_exito)
                logger.info("Importación exitosa - Redirigiendo al dashboard")

                return redirect('entrenos:dashboard_liftin')

            except Exception as e:
                logger.error(f"Error al procesar formulario: {str(e)}")
                logger.exception("Traceback completo:")
                messages.error(request, f"Error al importar entrenamiento: {str(e)}")
                return redirect('entrenos:importar_liftin_completo')

    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        logger.exception("Traceback completo:")
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect('entrenos:dashboard_liftin')


@login_required
def importar_liftin_basico(request):
    """
    Vista para importación básica de Liftin (versión simplificada)
    """
    if request.method == 'POST':
        form = ImportarLiftinBasicoForm(request.POST)

        if form.is_valid():
            entrenamiento = form.save()
            messages.success(request, '✅ Entrenamiento básico de Liftin importado exitosamente!')
            return redirect('entrenos:dashboard_liftin')
        else:
            messages.error(request, '❌ Error en el formulario. Revisa los datos ingresados.')
    else:
        form = ImportarLiftinBasicoForm()

    context = {
        'form': form,
        'title': 'Importar Entrenamiento Básico de Liftin',
    }

    return render(request, 'entrenos/importar_liftin_basico.html', context)


# ============================================================================
# VISTAS DE BÚSQUEDA Y LISTADO
# ============================================================================

@login_required
def buscar_entrenamientos_liftin(request):
    """
    Vista para buscar entrenamientos con filtros específicos de Liftin
    """
    form = BuscarEntrenamientosLiftinForm(request.GET or None)
    entrenamientos = EntrenoRealizado.objects.all().order_by('-fecha', '-hora_inicio')

    if form.is_valid():
        # Aplicar filtros
        if form.cleaned_data['cliente']:
            entrenamientos = entrenamientos.filter(cliente=form.cleaned_data['cliente'])

        if form.cleaned_data['fuente_datos']:
            entrenamientos = entrenamientos.filter(fuente_datos=form.cleaned_data['fuente_datos'])

        if form.cleaned_data['volumen_rango']:
            volumen = form.cleaned_data['volumen_rango']
            if volumen == 'bajo':
                entrenamientos = entrenamientos.filter(volumen_total_kg__lt=10000)
            elif volumen == 'medio':
                entrenamientos = entrenamientos.filter(volumen_total_kg__gte=10000, volumen_total_kg__lte=20000)
            elif volumen == 'alto':
                entrenamientos = entrenamientos.filter(volumen_total_kg__gt=20000)

        if form.cleaned_data['numero_ejercicios_min']:
            entrenamientos = entrenamientos.filter(numero_ejercicios__gte=form.cleaned_data['numero_ejercicios_min'])

        if form.cleaned_data['numero_ejercicios_max']:
            entrenamientos = entrenamientos.filter(numero_ejercicios__lte=form.cleaned_data['numero_ejercicios_max'])

        if form.cleaned_data['fecha_desde']:
            entrenamientos = entrenamientos.filter(fecha__gte=form.cleaned_data['fecha_desde'])

        if form.cleaned_data['fecha_hasta']:
            entrenamientos = entrenamientos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])

    # Paginación
    paginator = Paginator(entrenamientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas de la búsqueda
    stats = {
        'total': entrenamientos.count(),
        'liftin': entrenamientos.filter(fuente_datos='liftin').count(),
        'manual': entrenamientos.filter(fuente_datos='manual').count(),
        'volumen_total': entrenamientos.aggregate(Sum('volumen_total_kg'))['volumen_total_kg__sum'] or 0,
    }

    context = {
        'form': form,
        'page_obj': page_obj,
        'stats': stats,
        'title': 'Buscar Entrenamientos',
    }

    return render(request, 'entrenos/buscar_entrenamientos_liftin.html', context)


@login_required
def detalle_ejercicios_liftin(request, entrenamiento_id):
    """
    Vista para mostrar detalles de ejercicios específicos de un entrenamiento de Liftin
    """
    entrenamiento = get_object_or_404(EntrenoRealizado, id=entrenamiento_id)
    ejercicios = EjercicioLiftinDetallado.objects.filter(entreno=entrenamiento).order_by('orden_ejercicio')

    # Calcular estadísticas de ejercicios
    stats_ejercicios = {
        'total_ejercicios': ejercicios.count(),
        'completados': ejercicios.filter(estado_liftin='completado').count(),
        'fallados': ejercicios.filter(estado_liftin='fallado').count(),
        'nuevos': ejercicios.filter(estado_liftin='nuevo').count(),
        'volumen_total': sum([ej.volumen_ejercicio for ej in ejercicios]),
    }

    context = {
        'entrenamiento': entrenamiento,
        'ejercicios': ejercicios,
        'stats': stats_ejercicios,
        'title': f'Ejercicios - {entrenamiento.nombre_rutina_liftin or entrenamiento.rutina.nombre}',
    }

    return render(request, 'entrenos/detalle_ejercicios_liftin.html', context)


# ============================================================================
# VISTAS DE EXPORTACIÓN Y ANÁLISIS
# ============================================================================

@login_required
def exportar_datos_liftin(request):
    """
    Vista para exportar datos específicos de Liftin
    """
    if request.method == 'POST':
        form = ExportarDatosForm(request.POST)

        if form.is_valid():
            formato = form.cleaned_data['formato']
            incluir_liftin = form.cleaned_data['incluir_liftin']
            incluir_manual = form.cleaned_data['incluir_manual']
            fecha_desde = form.cleaned_data['fecha_desde']
            fecha_hasta = form.cleaned_data['fecha_hasta']

            # Filtrar entrenamientos
            entrenamientos = EntrenoRealizado.objects.all()

            fuentes = []
            if incluir_liftin:
                fuentes.append('liftin')
            if incluir_manual:
                fuentes.append('manual')

            if fuentes:
                entrenamientos = entrenamientos.filter(fuente_datos__in=fuentes)

            if fecha_desde:
                entrenamientos = entrenamientos.filter(fecha__gte=fecha_desde)

            if fecha_hasta:
                entrenamientos = entrenamientos.filter(fecha__lte=fecha_hasta)

            # Generar exportación según formato
            if formato == 'csv':
                return exportar_csv_liftin(entrenamientos)
            elif formato == 'json':
                return exportar_json_liftin(entrenamientos)
            elif formato == 'pdf':
                return exportar_pdf_liftin(entrenamientos)
    else:
        form = ExportarDatosForm()

    context = {
        'form': form,
        'title': 'Exportar Datos de Liftin',
    }

    return render(request, 'entrenos/exportar_datos_liftin.html', context)


def exportar_csv_liftin(entrenamientos):
    """
    Exportar entrenamientos a formato CSV
    """
    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = f'attachment; filename="entrenamientos_liftin_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Cliente', 'Rutina', 'Fuente', 'Hora Inicio', 'Hora Fin',
        'Duración (min)', 'Ejercicios', 'Volumen (kg)', 'Calorías',
        'FC Promedio', 'FC Máxima', 'Notas'
    ])

    for entreno in entrenamientos:
        writer.writerow([
            entreno.fecha,
            entreno.cliente.nombre,
            entreno.nombre_rutina_liftin or entreno.rutina.nombre,
            entreno.get_fuente_datos_display(),
            entreno.hora_inicio or '',
            entreno.hora_fin or '',
            entreno.duracion_minutos or '',
            entreno.numero_ejercicios or '',
            entreno.volumen_total_kg or '',
            entreno.calorias_quemadas or '',
            entreno.frecuencia_cardiaca_promedio or '',
            entreno.frecuencia_cardiaca_maxima or '',
            entreno.notas_liftin or ''
        ])

    return response


def exportar_json_liftin(entrenamientos):
    """
    Exportar entrenamientos a formato JSON
    """
    data = []

    for entreno in entrenamientos:
        ejercicios = []
        if hasattr(entreno, 'ejercicios_liftin'):
            ejercicios = [
                {
                    'nombre': ej.nombre_ejercicio,
                    'peso_formateado': ej.peso_formateado,
                    'repeticiones_formateado': ej.repeticiones_formateado,
                    'estado': ej.estado_liftin,
                    'orden': ej.orden_ejercicio,
                }
                for ej in entreno.ejercicios_liftin.all()
            ]

        data.append({
            'id': entreno.id,
            'fecha': entreno.fecha.isoformat(),
            'cliente': entreno.cliente.nombre,
            'rutina': entreno.nombre_rutina_liftin or entreno.rutina.nombre,
            'fuente_datos': entreno.fuente_datos,
            'hora_inicio': entreno.hora_inicio.isoformat() if entreno.hora_inicio else None,
            'hora_fin': entreno.hora_fin.isoformat() if entreno.hora_fin else None,
            'duracion_minutos': entreno.duracion_minutos,
            'numero_ejercicios': entreno.numero_ejercicios,
            'volumen_total_kg': float(entreno.volumen_total_kg) if entreno.volumen_total_kg else None,
            'volumen_total_formateado': entreno.volumen_total_formateado,
            'calorias_quemadas': entreno.calorias_quemadas,
            'frecuencia_cardiaca_promedio': entreno.frecuencia_cardiaca_promedio,
            'frecuencia_cardiaca_maxima': entreno.frecuencia_cardiaca_maxima,
            'notas_liftin': entreno.notas_liftin,
            'ejercicios': ejercicios,
        })

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response[
        'Content-Disposition'] = f'attachment; filename="entrenamientos_liftin_{timezone.now().strftime("%Y%m%d")}.json"'

    return response


@login_required
def comparar_liftin_manual(request):
    """
    Vista para comparar entrenamientos de Liftin vs manuales
    """
    # Estadísticas comparativas
    stats_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin').aggregate(
        total=Count('id'),
        duracion_promedio=Avg('duracion_minutos'),
        calorias_promedio=Avg('calorias_quemadas'),
        volumen_total=Sum('volumen_total_kg'),
        ejercicios_promedio=Avg('numero_ejercicios'),
    )

    stats_manual = EntrenoRealizado.objects.filter(fuente_datos='manual').aggregate(
        total=Count('id'),
        duracion_promedio=Avg('duracion_minutos'),
        calorias_promedio=Avg('calorias_quemadas'),
        volumen_total=Sum('volumen_total_kg'),
        ejercicios_promedio=Avg('numero_ejercicios'),
    )

    # Entrenamientos recientes de cada tipo
    liftin_recientes = EntrenoRealizado.objects.filter(fuente_datos='liftin').order_by('-fecha')[:10]
    manual_recientes = EntrenoRealizado.objects.filter(fuente_datos='manual').order_by('-fecha')[:10]

    context = {
        'stats_liftin': stats_liftin,
        'stats_manual': stats_manual,
        'liftin_recientes': liftin_recientes,
        'manual_recientes': manual_recientes,
        'title': 'Comparación Liftin vs Manual',
    }

    return render(request, 'entrenos/comparar_liftin_manual.html', context)


# ============================================================================
# APIS PARA DATOS DINÁMICOS
# ============================================================================

@login_required
def api_stats_liftin(request):
    """
    API para estadísticas específicas de Liftin
    """
    entrenamientos_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin')

    stats = {
        'total_entrenamientos': entrenamientos_liftin.count(),
        'volumen_total': entrenamientos_liftin.aggregate(Sum('volumen_total_kg'))['volumen_total_kg__sum'] or 0,
        'calorias_total': entrenamientos_liftin.aggregate(Sum('calorias_quemadas'))['calorias_quemadas__sum'] or 0,
        'duracion_promedio': entrenamientos_liftin.aggregate(Avg('duracion_minutos'))['duracion_minutos__avg'] or 0,
        'ejercicios_promedio': entrenamientos_liftin.aggregate(Avg('numero_ejercicios'))['numero_ejercicios__avg'] or 0,
        'fc_promedio': entrenamientos_liftin.aggregate(Avg('frecuencia_cardiaca_promedio'))[
                           'frecuencia_cardiaca_promedio__avg'] or 0,
    }

    # Datos para gráficos por mes
    entrenamientos_por_mes = []
    for i in range(6):  # Últimos 6 meses
        fecha = timezone.now().date() - timedelta(days=30 * i)
        mes_inicio = fecha.replace(day=1)
        if i == 0:
            mes_fin = fecha
        else:
            mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        count = entrenamientos_liftin.filter(fecha__gte=mes_inicio, fecha__lte=mes_fin).count()
        entrenamientos_por_mes.append({
            'mes': mes_inicio.strftime('%Y-%m'),
            'count': count
        })

    stats['entrenamientos_por_mes'] = list(reversed(entrenamientos_por_mes))

    return JsonResponse(stats)


@login_required
def api_ejercicios_liftin(request, entrenamiento_id):
    """
    API para obtener ejercicios específicos de un entrenamiento de Liftin
    """
    entrenamiento = get_object_or_404(EntrenoRealizado, id=entrenamiento_id)
    ejercicios = EjercicioLiftinDetallado.objects.filter(entreno=entrenamiento).order_by('orden_ejercicio')

    data = [
        {
            'id': ej.id,
            'nombre': ej.nombre_ejercicio,
            'orden': ej.orden_ejercicio,
            'peso_formateado': ej.peso_formateado,
            'peso_kg': float(ej.peso_kg) if ej.peso_kg else None,
            'repeticiones_formateado': ej.repeticiones_formateado,
            'series': ej.series_realizadas,
            'repeticiones_min': ej.repeticiones_min,
            'repeticiones_max': ej.repeticiones_max,
            'estado': ej.estado_liftin,
            'completado': ej.completado,
            'volumen': ej.volumen_ejercicio,
            'notas': ej.notas_ejercicio,
        }
        for ej in ejercicios
    ]

    return JsonResponse({'ejercicios': data})


# ============================================================================
# VISTAS DE UTILIDADES
# ============================================================================

@login_required
def validar_datos_liftin(request):
    """
    Vista para validar y limpiar datos de Liftin
    """
    if request.method == 'POST':
        # Lógica para validar y limpiar datos
        entrenamientos_problemas = EntrenoRealizado.objects.filter(
            fuente_datos='liftin'
        ).filter(
            Q(volumen_total_kg__isnull=True) |
            Q(numero_ejercicios__isnull=True) |
            Q(duracion_minutos__isnull=True)
        )

        # Intentar corregir datos faltantes
        corregidos = 0
        for entreno in entrenamientos_problemas:
            if not entreno.numero_ejercicios:
                ejercicios_count = entreno.ejercicios_liftin.count()
                if ejercicios_count > 0:
                    entreno.numero_ejercicios = ejercicios_count
                    entreno.save()
                    corregidos += 1

        messages.success(request, f'✅ Se corrigieron {corregidos} entrenamientos.')
        return redirect('entrenos:dashboard_liftin')

    # Mostrar problemas encontrados
    problemas = EntrenoRealizado.objects.filter(
        fuente_datos='liftin'
    ).filter(
        Q(volumen_total_kg__isnull=True) |
        Q(numero_ejercicios__isnull=True) |
        Q(duracion_minutos__isnull=True)
    )

    context = {
        'problemas': problemas,
        'title': 'Validar Datos de Liftin',
    }

    return render(request, 'entrenos/validar_datos_liftin.html', context)


@login_required
def preview_importacion(request):
    """
    Vista para previsualizar datos antes de importar
    """
    if request.method == 'POST':
        # Procesar datos de preview
        data = json.loads(request.body)

        # Validar datos
        errores = []
        warnings = []

        # Validaciones básicas
        if not data.get('cliente_id'):
            errores.append('Cliente es requerido')

        if not data.get('nombre_rutina'):
            errores.append('Nombre de rutina es requerido')

        # Validaciones de formato
        if data.get('tiempo_total') and not data['tiempo_total'].count(':') == 2:
            warnings.append('Formato de tiempo puede ser incorrecto (use H:MM:SS)')

        response_data = {
            'valido': len(errores) == 0,
            'errores': errores,
            'warnings': warnings,
            'datos_procesados': data,
        }

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# --- FIN DE LA VISTA resumen_entreno ---


from .models import RegistroWhoop
from .forms import RegistroWhoopForm

from django.shortcuts import redirect


@login_required
def registrar_whoop(request):
    if request.method == 'POST':
        form = RegistroWhoopForm(request.POST)
        if form.is_valid():
            fecha_hoy = timezone.now().date()
            registro, creado = RegistroWhoop.objects.get_or_create(
                cliente=request.user,
                fecha=fecha_hoy,
                defaults=form.cleaned_data
            )

            if not creado:
                # Si ya existe, actualiza los valores
                for campo, valor in form.cleaned_data.items():
                    setattr(registro, campo, valor)

            # Cálculo automático
            if registro.horas_sueno and registro.sueno_necesario:
                durmio = registro.horas_sueno.total_seconds() / 3600
                necesario = registro.sueno_necesario.total_seconds() / 3600
                registro.horas_vs_necesidad = round((durmio / necesario) * 100, 1)

            ultimos_7 = RegistroWhoop.objects.filter(
                cliente=request.user,
                fecha__gte=timezone.now().date() - timedelta(days=6)
            )
            registro.regularidad_sueno = ultimos_7.aggregate(Avg('sleep_performance'))['sleep_performance__avg'] or 0
            registro.eficiencia_sueno = ultimos_7.aggregate(Avg('recovery'))['recovery__avg'] or 0

            registro.save()
            return redirect('entrenos:tarjeta_whoop')
    else:
        form = RegistroWhoopForm()
    return render(request, 'entrenos/registro_whoop.html', {'form': form})


# views.py
@login_required
def editar_whoop(request, pk):
    registro = get_object_or_404(RegistroWhoop, pk=pk, cliente=request.user)
    if request.method == 'POST':
        form = RegistroWhoopForm(request.POST, instance=registro)
        if form.is_valid():
            registro = form.save(commit=False)
            # Cálculo de horas_vs_necesidad
            if registro.horas_sueno and registro.sueno_necesario:
                durmio = registro.horas_sueno.total_seconds() / 3600
                necesario = registro.sueno_necesario.total_seconds() / 3600
                registro.horas_vs_necesidad = round((durmio / necesario) * 100, 1)

            # Cálculo de regularidad y eficiencia (últimos 7 días hasta la fecha del registro)
            ultimos_7 = RegistroWhoop.objects.filter(
                cliente=registro.cliente,
                fecha__gte=registro.fecha - timedelta(days=6),
                fecha__lte=registro.fecha
            )
            registro.regularidad_sueno = ultimos_7.aggregate(Avg('sleep_performance'))['sleep_performance__avg'] or 0
            registro.eficiencia_sueno = ultimos_7.aggregate(Avg('recovery'))['recovery__avg'] or 0

            # recalcular aquí los campos automáticos si quieres
            registro.save()
            return redirect('entrenos:tarjeta_whoop')
    else:
        form = RegistroWhoopForm(instance=registro)
    return render(request, 'entrenos/registro_whoop.html', {'form': form, 'editar': True})


from clientes.models import Cliente

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from .models import RegistroWhoop
from clientes.models import Cliente
from entrenos.utils.utils import analizar_entreno_whoop  # Asegúrate de tener esta función en utils

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from .models import RegistroWhoop
from clientes.models import Cliente


@login_required
def tarjeta_whoop(request):
    # Datos del usuario
    registro = RegistroWhoop.objects.filter(cliente=request.user).order_by('-fecha').first()
    cliente = Cliente.objects.filter(user=request.user).first()
    registros_whoop = RegistroWhoop.objects.filter(cliente=request.user).order_by('-fecha')

    # Consejo diario si hay registro
    if registro:
        consejo_entreno, color_entreno = analizar_entreno_whoop(registro)
    else:
        consejo_entreno = None
        color_entreno = None

    # Últimos 7 días
    desde_fecha = timezone.now().date() - timedelta(days=6)
    ultimos_dias = registros_whoop.filter(fecha__gte=desde_fecha)

    # Cálculo de promedios
    strain_medio = ultimos_dias.aggregate(Avg('strain'))['strain__avg'] or 0
    recovery_medio = ultimos_dias.aggregate(Avg('recovery'))['recovery__avg'] or 0
    horas_sueno_media = ultimos_dias.aggregate(Avg('horas_sueno'))['horas_sueno__avg'] or 0

    # Análisis inteligente semanal de Joi
    def analizar_estado_semanal(strain, recovery, sueno_horas):
        # Strain
        if strain < 7:
            strain_info = "🔵 Baja carga <7 → Puedes entrenar más fuerte o añadir volumen."
        elif 7 <= strain <= 10:
            strain_info = "🟢 Óptima carga estás entre 7 y 10 → Buen equilibrio esfuerzo-recuperación."
        else:
            strain_info = "🔴 Alta carga → Riesgo de fatiga. Cuida el sueño y evita sobreentreno."

        # Recovery
        if recovery < 60:
            recovery_info = "🔴 Recuperación pobre → Reduce la intensidad y prioriza el descanso."
        elif 60 <= recovery <= 80:
            recovery_info = "🟡 Recuperación aceptable → Controla la intensidad día a día."
        else:
            recovery_info = "🟢 Excelente recuperación → Ideal para progresar con fuerza/hipertrofia."

        # Sueño
        if sueno_horas < 6:
            sueno_info = "🔴 Sueño insuficiente → Aumenta el riesgo de fatiga hormonal."
        elif 6 <= sueno_horas < 7:
            sueno_info = "🟡 Sueño aceptable si compensas con siestas o descansos."
        elif 7 <= sueno_horas <= 8:
            sueno_info = "🟢 Sueño óptimo → Buen soporte para progresar."
        else:
            sueno_info = "💚 Sueño ideal → Perfecto para fases de volumen o alta intensidad."

        # Conclusión combinada
        if strain > 10 and recovery < 60:
            resumen = "⚠️ Posible sobreentreno. Reduce intensidad y prioriza descanso y sueño profundo."
        elif strain < 7 and recovery > 80:
            resumen = "💪 Estás listo para un ciclo fuerte. Momento ideal para subir peso o volumen."
        elif 7 <= strain <= 10 and 60 <= recovery <= 80 and sueno_horas >= 7:
            resumen = "📈 Equilibrio sólido. Puedes seguir progresando con control."
        elif recovery > 80 and sueno_horas > 7:
            resumen = "🌟 Ventana de oro → Aprovecha para progresar en fuerza o hipertrofia."
        else:
            resumen = "🌀 Escucha tu cuerpo y ajusta según sensaciones. No hay señales de alarma."

        return strain_info, recovery_info, sueno_info, resumen

    # Ejecutar análisis
    if hasattr(horas_sueno_media, 'total_seconds'):
        sueno_horas_float = horas_sueno_media.total_seconds() / 3600
    else:
        sueno_horas_float = float(horas_sueno_media) / 3600

    strain_i, recovery_i, sueno_i, resumen_joi = analizar_estado_semanal(
        strain_medio, recovery_medio, sueno_horas_float
    )
    valores = ultimos_dias.aggregate(
        necesidad=Avg('horas_vs_necesidad'),
        regularidad=Avg('regularidad_sueno'),
        eficiencia=Avg('eficiencia_sueno'),
    )

    def interpretar_metrica(valor, optimo, suficiente, tipo="↑ bueno / ↓ malo"):
        if valor is None:
            return "Sin datos"

        if tipo == "↑ bueno / ↓ malo":
            if valor >= optimo:
                return "🟢 Óptimo"
            elif valor >= suficiente:
                return "🟡 Suficiente"
            else:
                return "🔴 Deficiente"
        elif tipo == "↓ bueno / ↑ malo":
            if valor < optimo:
                return "🟢 Óptimo"
            elif valor < suficiente:
                return "🟡 Suficiente"
            else:
                return "🔴 Deficiente"

    interpretaciones = {
        'horas_vs_necesidad': interpretar_metrica(valores['necesidad'], 85, 70),
        'regularidad_sueno': interpretar_metrica(valores['regularidad'], 80, 70),
        'eficiencia_sueno': interpretar_metrica(valores['eficiencia'], 85, 70),
    }
    return render(request, 'entrenos/tarjeta_whoop.html', {
        'cliente': cliente,
        'user': request.user,
        'registro': registro,
        'registros_whoop': registros_whoop,
        'consejo_entreno': consejo_entreno,
        'color_entreno': color_entreno,
        'strain_medio': strain_medio,
        'recovery_medio': recovery_medio,
        'horas_sueno_media': horas_sueno_media,
        'analisis_strain': strain_i,
        'analisis_recovery': recovery_i,
        'analisis_sueno': sueno_i,
        'conclusion_joi': resumen_joi,
        'interpretaciones': interpretaciones,
    })


def gestionar_ejercicios_base(request):
    # Lógica para AÑADIR un nuevo ejercicio
    # Usamos un nombre único para el botón de submit para diferenciar acciones
    if request.method == 'POST' and 'add_exercise' in request.POST:
        form = EjercicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Ejercicio añadido a la base de datos correctamente!')
            return redirect('gestionar_ejercicios_base')  # Redirigimos a la misma página
        else:
            # Si el formulario no es válido, los errores se mostrarán en el template
            messages.error(request, 'Hubo un error. Por favor, revisa los campos del formulario.')

    # Lógica para ELIMINAR los ejercicios seleccionados
    if request.method == 'POST' and 'delete_selected' in request.POST:
        ejercicio_ids_a_eliminar = request.POST.getlist('ejercicio_ids')
        if not ejercicio_ids_a_eliminar:
            messages.warning(request, 'No has seleccionado ningún ejercicio para eliminar.')
        else:
            # Eliminamos los ejercicios de la BD que coincidan con los IDs seleccionados
            EjercicioBase.objects.filter(id__in=ejercicio_ids_a_eliminar).delete()
            count = len(ejercicio_ids_a_eliminar)
            messages.success(request, f'Se han eliminado {count} ejercicio(s) correctamente.')
        return redirect('gestionar_ejercicios_base')

    # Lógica para MOSTRAR la lista (método GET o después de una acción)

    # Búsqueda
    query = request.GET.get('buscar', '')
    ejercicios_list = EjercicioBase.objects.all().order_by('grupo_muscular', 'nombre')
    if query:
        ejercicios_list = ejercicios_list.filter(nombre__icontains=query)

    # Paginación
    paginator = Paginator(ejercicios_list, 15)  # 15 ejercicios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Creamos una instancia vacía del formulario para el panel de "Añadir Ejercicio"
    form_para_anadir = EjercicioForm()

    context = {
        'page_obj': page_obj,
        'form_para_anadir': form_para_anadir,
        'total_ejercicios': paginator.count,
        'query': query,
    }
    # Asegúrate de que la ruta al template sea correcta
    return render(request, 'entrenos/gestionar_ejercicios_base.html', context)


# entrenos/views.py

# ... (otros imports que ya tengas) ...
from django.shortcuts import render
from clientes.models import Cliente
# entrenos/views.py

# entrenos/views.py

# ... (tus otros imports) ...
import json
from datetime import datetime  # Asegúrate de que este import esté presente


# en entrenos/views.py

@login_required
def vista_entrenamiento_activo(request, cliente_id):
    """
    Muestra el formulario interactivo para que el usuario registre
    las series de su entrenamiento del día.
    VERSIÓN MEJORADA para incluir el peso recomendado.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    try:
        fecha_str = request.GET.get('fecha')
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        fecha_para_template = fecha_obj.strftime('%Y-%m-%d')

        rutina_nombre = request.GET.get('rutina_nombre')
        ejercicios_planificados_json = request.GET.get('ejercicios', '[]')
        ejercicios_planificados = json.loads(ejercicios_planificados_json)
        leyenda_rpe = {
            "10": "Máximo esfuerzo, no podrías hacer ni una repetición más.",
            "9": "Muy intenso, podrías hacer 1 repetición más como máximo.",
            "8": "Intenso, podrías hacer 2-3 repeticiones más.",
            "7": "Moderado, podrías hacer 3-4 repeticiones más.",
            "6": "Fácil, podrías hacer muchas repeticiones más.",
        }
        # --- INICIO DE LA CORRECCIÓN ---
        # Preparamos los datos para la plantilla, asegurando que los valores existan
        for i, ejercicio in enumerate(ejercicios_planificados):
            ejercicio['form_id'] = f'ejercicio_{i}'

            # Obtener repeticiones objetivo (el valor más bajo del rango)
            try:
                reps_str = str(ejercicio.get('repeticiones', '8'))
                ejercicio['reps_objetivo'] = int(reps_str.split('-')[0].strip())
            except:
                ejercicio['reps_objetivo'] = 8  # Fallback

            # Obtener peso recomendado
            # Usamos .get() para evitar errores si la clave no existe
            ejercicio['peso_recomendado_kg'] = ejercicio.get('peso_kg', 0.0)
            ejercicio['rpe_objetivo'] = ejercicio.get('rpe_objetivo', 8)
            ejercicio['tempo'] = ejercicio.get('tempo', '2-0-X-0')  # Valor por defecto
            ejercicio['descanso_minutos'] = ejercicio.get('descanso_minutos', 2)  # Valor por defecto
    except Exception as e:
        messages.error(request, f"Error al cargar los datos del entrenamiento: {e}")
        return redirect('entrenos:vista_plan_anual', cliente_id=cliente.id)

    context = {
        'cliente': cliente,
        'fecha': fecha_para_template,
        'rutina_nombre': rutina_nombre,
        'ejercicios_planificados': ejercicios_planificados,
        'leyenda_rpe': leyenda_rpe,
    }
    try:
        from .gamificacion_service import EntrenamientoGamificacionService
        resumen_gamificacion = EntrenamientoGamificacionService.obtener_resumen_gamificacion(cliente)
        context['resumen_gamificacion'] = resumen_gamificacion
    except Exception as e:
        print(f"Error obteniendo resumen gamificación: {e}")
        context['resumen_gamificacion'] = {'tiene_perfil': False}
    return render(request, 'entrenos/entrenamiento_activo.html', context)


# en entrenos/views.py
# en entrenos/views.py

# --- Asegúrate de tener estas importaciones al principio del archivo ---
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import EntrenoRealizado, EjercicioRealizado
from rutinas.models import Rutina
from clientes.models import Cliente
from analytics.monitor_adherencia import MonitorAdherencia, SesionEntrenamiento


# --------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def guardar_entrenamiento_activo(request, cliente_id):
    """
    VERSIÓN FINAL: Guarda el entrenamiento en EjercicioRealizado, calcula
    métricas y registra la sesión en el MonitorAdherencia.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    print("\\n--- INICIANDO GUARDADO DE ENTRENAMIENTO ACTIVO ---")

    try:
        # --- 1. Crear el objeto EntrenoRealizado principal ---
        fecha_str = request.POST.get('fecha')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        rutina_nombre = request.POST.get('rutina_nombre')
        rutina_obj, _ = Rutina.objects.get_or_create(nombre=rutina_nombre)

        entreno = EntrenoRealizado.objects.create(
            cliente=cliente,
            fecha=fecha,
            rutina=rutina_obj,
            fuente_datos='manual',
            duracion_minutos=request.POST.get('duracion_minutos') or None,
            calorias_quemadas=request.POST.get('calorias_quemadas') or None,
            notas_liftin=request.POST.get('notas_liftin', '').strip()
        )
        print(f"-> Creado EntrenoRealizado ID: {entreno.id}")

        # --- 2. Procesar y guardar ejercicios ---
        volumen_total_entreno = Decimal('0.0')
        ejercicios_procesados_count = 0
        ejercicio_form_ids = [k.replace('_nombre', '') for k in request.POST if k.endswith('_nombre')]

        for form_id in ejercicio_form_ids:
            ejercicio_nombre = request.POST.get(f'{form_id}_nombre', '').strip().title()
            if not ejercicio_nombre:
                continue

            print(f"-> Procesando ejercicio: {ejercicio_nombre}")

            series_validas = 0
            reps_totales = 0
            peso_total_sumado = Decimal('0.0')
            series_completadas = 0
            volumen_ejercicio = Decimal('0.0')

            for i in range(1, 11):
                peso_key = f"{form_id}_peso_{i}"
                reps_key = f"{form_id}_reps_{i}"
                if peso_key not in request.POST or reps_key not in request.POST:
                    break
                try:
                    peso_str = request.POST.get(peso_key, '0').replace(',', '.')
                    reps_str = request.POST.get(reps_key, '0')
                    completado = request.POST.get(f"{form_id}_completado_{i}") == "1"
                    peso = Decimal(peso_str) if peso_str else Decimal('0')
                    reps = int(reps_str) if reps_str else 0

                    if peso > 0 or reps > 0:
                        series_validas += 1
                        reps_totales += reps
                        peso_total_sumado += peso
                        volumen_ejercicio += (peso * reps)
                        if completado:
                            series_completadas += 1
                except (ValueError, TypeError, InvalidOperation) as e:
                    print(f"   ⚠️ Error en datos de serie {i}: {e}")
                    continue

            if series_validas > 0:
                peso_promedio = peso_total_sumado / series_validas
                repeticiones_promedio = reps_totales // series_validas
                ejercicio_completado = series_completadas == series_validas
                EjercicioRealizado.objects.create(
                    entreno=entreno, nombre_ejercicio=ejercicio_nombre, grupo_muscular="Otros",
                    peso_kg=float(peso_promedio), series=series_validas,
                    repeticiones=repeticiones_promedio, completado=ejercicio_completado,
                    fuente_datos='manual'
                )
                print(f"   -> Creado EjercicioRealizado: {ejercicio_nombre} ({series_validas} series)")
                volumen_total_entreno += volumen_ejercicio
                ejercicios_procesados_count += 1

        # --- 3. Actualizar el EntrenoRealizado con los totales finales ---
        entreno.volumen_total_kg = volumen_total_entreno
        entreno.numero_ejercicios = ejercicios_procesados_count
        entreno.save(update_fields=['volumen_total_kg', 'numero_ejercicios'])
        print("-> Entrenamiento guardado y actualizado con éxito.")

        # --- 4. PROCESAR GAMIFICACIÓN (CÓDIGO CORREGIDO) ---
        try:
            from .gamificacion_service import EntrenamientoGamificacionService

            # Procesar gamificación usando 'entreno' (no 'entreno_realizado')
            resultado_gamificacion = EntrenamientoGamificacionService.procesar_entrenamiento_completado(
                entreno  # <-- VARIABLE CORRECTA
            )

            # Verificar si hubo errores
            if 'error' not in resultado_gamificacion:
                # Mensaje principal de puntos ganados
                messages.success(
                    request,
                    f"🎉 ¡Entrenamiento guardado! +{resultado_gamificacion['puntos_totales']} puntos ganados"
                )

                # Desglose de puntos si hay bonus o pruebas
                if resultado_gamificacion['puntos_bonus'] > 0 or resultado_gamificacion['puntos_pruebas'] > 0:
                    messages.info(
                        request,
                        f"💰 Desglose: {resultado_gamificacion['puntos_base']} base + "
                        f"{resultado_gamificacion['puntos_bonus']} bonus + "
                        f"{resultado_gamificacion['puntos_pruebas']} pruebas"
                    )

                # Mensajes por pruebas completadas
                for prueba in resultado_gamificacion['pruebas_completadas']:
                    messages.success(
                        request,
                        f"⚔️ ¡Prueba completada: {prueba.nombre}! +{prueba.puntos_recompensa} puntos"
                    )

                # Mensaje de ascensión si ocurrió
                if resultado_gamificacion['ascension']:
                    messages.success(
                        request,
                        f"🔥 ¡ASCENSIÓN! Nuevo nivel: {resultado_gamificacion['nivel_nuevo']}"
                    )
                    messages.info(
                        request,
                        f"🎯 Has evolucionado de {resultado_gamificacion['nivel_anterior']} "
                        f"a {resultado_gamificacion['nivel_nuevo']}"
                    )

                # Información de racha si existe
                racha = EntrenamientoGamificacionService._calcular_racha_actual(cliente)
                if racha > 1:
                    messages.info(
                        request,
                        f"🔥 ¡Racha de {racha} días consecutivos! Sigue así"
                    )
            else:
                # Si hubo error en gamificación, solo mostrar mensaje básico
                print(f"Error en gamificación: {resultado_gamificacion['error']}")
                messages.success(request, "Entrenamiento guardado correctamente")

        except ImportError:
            # Si no existe el servicio de gamificación
            print("Servicio de gamificación no encontrado")
            messages.success(request, "Entrenamiento guardado correctamente")

        except Exception as e:
            # Cualquier otro error en gamificación
            print(f"Error procesando gamificación: {e}")
            messages.success(request, "Entrenamiento guardado correctamente")
        # --- 5. Redirección al Dashboard de Analíticas ---
        messages.success(request, "¡Entrenamiento guardado! Analizando tu progreso...")
        return redirect('analytics:dashboard_cliente', cliente_id=cliente.id)

    except Exception as e:
        print(f"\n--- ❌ ERROR CRÍTICO DURANTE EL GUARDADO: {e} ---")
        import traceback
        traceback.print_exc()
        if 'entreno' in locals() and entreno.pk:
            entreno.delete()
        messages.error(request, f"Hubo un error crítico al guardar: {e}")
        return redirect('entrenos:vista_plan_anual', cliente_id=cliente_id)


# en entrenos/views.py

# --- Asegúrate de tener todas estas importaciones al principio del archivo ---
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from clientes.models import Cliente
from analytics.planificador_helms_completo import PlanificadorHelms, crear_perfil_desde_cliente
from analytics.views import CalculadoraEjerciciosTabla
from analytics.validador_jerarquia_helms import validar_adherencia_basica
from analytics.sistema_educacion_helms import agregar_educacion_a_plan
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import calendar


# --------------------------------------------------------------------------


def vista_plan_anual(request, cliente_id):
    """
    Vista para generar y mostrar el plan anual de Helms.
    VERSIÓN FINAL CON VALIDACIÓN Y SISTEMA EDUCATIVO INTEGRADO.
    """
    try:
        # --- PASO 1: Obtener cliente y datos de navegación del calendario ---
        cliente_obj = get_object_or_404(Cliente, id=cliente_id)
        año_actual = int(request.GET.get('año', date.today().year))
        mes_actual = int(request.GET.get('mes', date.today().month))

        # --- PASO 2: Calcular 1RM ---
        maximos_actuales = {}
        try:
            calculadora_rm = CalculadoraEjerciciosTabla(cliente_obj)
            ejercicios_con_rm = calculadora_rm.obtener_ejercicios_tabla()
            for e in ejercicios_con_rm:
                try:
                    nombre_limpio = e.get('nombre', '').strip().lower()
                    peso_str = str(e.get('peso', '0')).replace(',', '.')
                    reps_valor = e.get('repeticiones', '0')
                    reps_str = str(reps_valor).split('-')[0].strip() if isinstance(reps_valor, str) else str(reps_valor)
                    if nombre_limpio and peso_str.replace('.', '', 1).isdigit() and reps_str.isdigit():
                        peso, reps = Decimal(peso_str), int(reps_str)
                        if peso > 0 and reps > 0:
                            rm_estimado = peso * (1 + Decimal(reps) / Decimal(30))
                            if nombre_limpio not in maximos_actuales or rm_estimado > maximos_actuales[nombre_limpio]:
                                maximos_actuales[nombre_limpio] = float(rm_estimado)
                except (ValueError, TypeError, InvalidOperation):
                    continue
        except Exception:
            maximos_actuales = {'press_banca': 80.0, 'sentadilla': 100.0}
        print(f"✅ Máximos calculados: {len(maximos_actuales)} ejercicios")

        # --- PASO 3: Crear perfil y VALIDAR ADHERENCIA ---
        perfil = crear_perfil_desde_cliente(cliente_obj)
        one_rm_normalizados = {str(k).lower().strip(): v for k, v in maximos_actuales.items()}
        # 2. Inyectamos el diccionario NORMALIZADO en el perfil
        perfil.maximos_actuales = one_rm_normalizados

        validacion_adherencia = validar_adherencia_basica(perfil)

        if not validacion_adherencia.puede_avanzar:
            context = {
                'cliente': cliente_obj, 'error': True, 'validacion_fallida': True,
                'validacion': validacion_adherencia,
            }
            print(f"❌ Validación de Adherencia fallida: {validacion_adherencia.recomendaciones}")
            return render(request, 'entrenos/vista_plan_calendario.html', context)

        print("✅ Validación de Adherencia superada.")

        # --- PASO 4: Generar y Enriquecer el Plan ---
        planificador = PlanificadorHelms(perfil)
        plan_original = planificador.generar_plan_anual()
        print(f"✅ Plan original generado.")

        plan = agregar_educacion_a_plan(plan_original)
        print("📚 Plan enriquecido con datos educativos.")

        if not plan or not isinstance(plan, dict):
            raise Exception("El plan generado está vacío o tiene un formato incorrecto.")

        # --- PASO 5: Preparar el contexto para la plantilla ---
        matriz_mes = calendar.monthcalendar(año_actual, mes_actual)
        hoy = date.today()
        primer_dia_mes = date(año_actual, mes_actual, 1)
        mes_anterior = primer_dia_mes - timedelta(days=1)
        mes_siguiente = (primer_dia_mes + timedelta(days=31)).replace(day=1)
        semanas_calendario = []
        entrenos_del_plan = plan.get('entrenos_por_fecha', {})

        for semana_matriz in matriz_mes:
            dias_semana = []
            for dia_num in semana_matriz:
                if dia_num == 0:
                    dias_semana.append(None)
                else:
                    fecha_actual = date(año_actual, mes_actual, dia_num)
                    fecha_str = fecha_actual.isoformat()
                    entrenamiento_dia = entrenos_del_plan.get(fecha_str)
                    if entrenamiento_dia:
                        try:
                            fase_nombre = entrenamiento_dia['nombre_rutina'].split(' - ')[1].lower().strip()
                            entrenamiento_dia['fase_css'] = f"fase-{fase_nombre}"
                        except (IndexError, AttributeError):
                            entrenamiento_dia['fase_css'] = "fase-default"
                    dias_semana.append({
                        "numero": dia_num, "es_hoy": fecha_actual == hoy,
                        "entrenamiento": entrenamiento_dia
                    })
            semanas_calendario.append(dias_semana)

        context = {
            'cliente': cliente_obj,
            'calendario': {
                'semanas': semanas_calendario, 'nombre_mes': calendar.month_name[mes_actual],
                'año': año_actual, 'mes_num': mes_actual
            },
            'nav': {
                'anterior': {'año': mes_anterior.year, 'mes': mes_anterior.month},
                'siguiente': {'año': mes_siguiente.year, 'mes': mes_siguiente.month}
            },
            'entrenos_por_fecha_data': json.dumps(entrenos_del_plan)
        }

        return render(request, 'entrenos/vista_plan_calendario.html', context)

    except Exception as e:
        print(f"❌ Error general en vista_plan_anual: {str(e)}")
        import traceback
        traceback.print_exc()
        error_context = {
            'error': True, 'error_message': str(e), 'error_type': type(e).__name__,
            'cliente': cliente_obj if 'cliente_obj' in locals() else None,
        }
        return render(request, 'entrenos/vista_plan_calendario.html', error_context)


# views.py - Actualizar tu vista existente
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from analytics.planificador_integrado import PlanificadorIntegrado


@login_required
def vista_plan_calendario(request, cliente_id):
    """
    Vista principal del plan - ahora con integración Helms
    """
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)

    try:
        # Usar el planificador integrado
        planificador = PlanificadorIntegrado(cliente_id)
        plan = planificador.generar_plan_anual()
        estadisticas = planificador.obtener_estadisticas_integracion()

        # Preparar contexto para el template
        contexto = {
            'cliente': cliente,
            'plan': plan,
            'estadisticas_helms': estadisticas,
            'tiene_datos_helms': 'datos_helms' in plan,
            'generado_por_helms': plan.get('metadata', {}).get('generado_por') == 'helms',

            # Información educativa sobre Helms
            'info_rpe': {
                6: "Muy fácil - Podrías hacer muchas repeticiones más",
                7: "Moderado - Podrías hacer 3-4 repeticiones más",
                8: "Intenso - Podrías hacer 2-3 repeticiones más",
                9: "Muy intenso - Podrías hacer 1-2 repeticiones más",
                10: "Máximo esfuerzo - Al fallo muscular"
            },

            'info_tempo': {
                'descripcion': 'Formato: Excéntrica-Pausa-Concéntrica-Pausa',
                'ejemplo': '2-0-X-0 = 2 seg bajada, sin pausa, explosiva subida, sin pausa'
            }
        }

        return render(request, 'entrenos/vista_plan_calendario.html', contexto)

    except Exception as e:
        # Log del error y fallback
        print(f"❌ Error en vista_plan_calendario: {str(e)}")

        # Fallback a tu sistema actual
        from .analytics.planificador import PlanificadorAnualIA
        planificador_fallback = PlanificadorAnualIA(cliente_id)
        plan_fallback = planificador_fallback.generar_plan()

        contexto = {
            'cliente': cliente,
            'plan': plan_fallback,
            'error_helms': True,
            'mensaje_error': 'Usando planificador de respaldo'
        }

        return render(request, 'entrenos/vista_plan_calendario.html', contexto)


@login_required
def api_regenerar_plan_helms(request, cliente_id):
    """
    API endpoint para regenerar plan con configuración específica
    """
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)

        # Obtener configuración del request
        usar_helms = request.POST.get('usar_helms', 'true') == 'true'
        incluir_validacion = request.POST.get('incluir_validacion', 'true') == 'true'

        try:
            planificador = PlanificadorIntegrado(cliente_id)
            planificador.usar_helms_como_principal = usar_helms
            planificador.incluir_validacion_helms = incluir_validacion

            plan = planificador.generar_plan_anual()
            estadisticas = planificador.obtener_estadisticas_integracion()

            return JsonResponse({
                'success': True,
                'plan_id': plan.get('id'),
                'generado_por': plan.get('metadata', {}).get('generado_por'),
                'estadisticas': estadisticas,
                'mensaje': '✅ Plan regenerado exitosamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'mensaje': '❌ Error al regenerar el plan'
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def dashboard_comparacion_planificadores(request, cliente_id):
    """
    Dashboard para comparar tu planificador actual vs Helms
    """
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)

    try:
        # Generar plan con ambos sistemas
        planificador_integrado = PlanificadorIntegrado(cliente_id)

        # Plan con Helms
        planificador_integrado.usar_helms_como_principal = True
        plan_helms = planificador_integrado.generar_plan_anual()

        # Plan con tu sistema actual
        planificador_integrado.usar_helms_como_principal = False
        plan_actual = planificador_integrado.generar_plan_anual()

        # Comparar métricas
        comparacion = {
            'volumen_total': {
                'helms': sum(plan_helms.get('datos_helms', {}).get('volumen_semanal', {}).values()),
                'actual': _calcular_volumen_plan(plan_actual)
            },
            'ejercicios_por_semana': {
                'helms': len(plan_helms.get('ejercicios_por_semana', {}).get('1', [])),
                'actual': len(plan_actual.get('ejercicios_por_semana', {}).get('1', []))
            },
            'tiempo_estimado': {
                'helms': _calcular_tiempo_plan(plan_helms),
                'actual': _calcular_tiempo_plan(plan_actual)
            }
        }

        contexto = {
            'cliente': cliente,
            'plan_helms': plan_helms,
            'plan_actual': plan_actual,
            'comparacion': comparacion
        }

        return render(request, 'dashboard_comparacion.html', contexto)

    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})


def _calcular_volumen_plan(plan: Dict) -> int:
    """Calcula volumen total de un plan"""
    volumen_total = 0
    for ejercicios in plan.get('ejercicios_por_semana', {}).values():
        for ejercicio in ejercicios:
            volumen_total += ejercicio.get('series', 0)
    return volumen_total


def _calcular_tiempo_plan(plan: Dict) -> int:
    """Calcula tiempo estimado de un plan en minutos"""
    tiempo_total = 0
    for ejercicios in plan.get('ejercicios_por_semana', {}).values():
        for ejercicio in ejercicios:
            series = ejercicio.get('series', 0)
            descanso = ejercicio.get('descanso_minutos', 3)
            tiempo_ejercicio = series * 2 + (series - 1) * descanso  # 2 min por serie + descansos
            tiempo_total += tiempo_ejercicio
    return tiempo_total // 7  # Promedio por día


# views.py - Uso del convertidor
from .utils.convertidor_formatos import ConvertidorFormatos, convertir_plan_para_vista, extraer_datos_educativos


@login_required
def vista_plan_calendario_con_conversion(request, cliente_id):
    """
    Vista que usa el convertidor para mantener compatibilidad
    """
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)

    try:
        # Generar plan con el sistema integrado
        planificador = PlanificadorIntegrado(cliente_id)
        plan_helms = planificador.generar_plan_anual()

        # Convertir a formato actual si es necesario
        if plan_helms.get('metadata', {}).get('generado_por') == 'helms':
            resultado_conversion = convertir_plan_para_vista(plan_helms)
            plan = resultado_conversion['plan']
            validacion = resultado_conversion['validacion']
        else:
            plan = plan_helms
            validacion = {'exitosa': True}

        # Extraer datos educativos
        datos_educativos = extraer_datos_educativos(plan)

        # Preparar contexto
        contexto = {
            'cliente': cliente,
            'plan': plan,
            'validacion_conversion': validacion,
            'datos_educativos': datos_educativos,
            'tiene_datos_helms': 'datos_helms' in plan,
            'generado_por_helms': plan.get('metadata', {}).get('generado_por') == 'helms'
        }

        return render(request, 'entrenos/vista_plan_calendario.html', contexto)

    except Exception as e:
        # Manejo de errores con logging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en vista_plan_calendario: {str(e)}")

        return render(request, 'error.html', {
            'error': 'Error al generar el plan',
            'detalle': str(e) if settings.DEBUG else 'Contacta al soporte'
        })


# en entrenos/views.py

# --- Asegúrate de que estas importaciones estén al principio del archivo ---
from .models import EntrenoRealizado, EjercicioRealizado
from clientes.models import Cliente
from analytics.planificador_helms_completo import PlanificadorHelms, crear_perfil_desde_cliente  # <-- ¡USA ESTE!
from analytics.views import CalculadoraEjerciciosTabla
from decimal import Decimal, InvalidOperation


# ... (otras importaciones que ya tengas)

def vista_resumen_anual(request, cliente_id):
    """
    Muestra una vista de alto nivel de todo el plan anual,
    organizado por mesociclos o bloques.
    VERSIÓN CORREGIDA para usar el planificador unificado.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # --- PASO 1: Calcular 1RM (Lógica idéntica a la vista del calendario) ---
    maximos_actuales = {}
    try:
        calculadora_rm = CalculadoraEjerciciosTabla(cliente)
        ejercicios_con_rm = calculadora_rm.obtener_ejercicios_tabla()
        for e in ejercicios_con_rm:
            try:
                nombre_limpio = e.get('nombre', '').strip().lower()
                peso_str = str(e.get('peso', '0')).replace(',', '.')
                reps_valor = e.get('repeticiones', '0')
                reps_str = str(reps_valor).split('-')[0].strip() if isinstance(reps_valor, str) else str(reps_valor)
                if nombre_limpio and peso_str.replace('.', '', 1).isdigit() and reps_str.isdigit():
                    peso, reps = Decimal(peso_str), int(reps_str)
                    if peso > 0 and reps > 0:
                        rm_estimado = peso * (1 + Decimal(reps) / Decimal(30))
                        if nombre_limpio not in maximos_actuales or rm_estimado > maximos_actuales[nombre_limpio]:
                            maximos_actuales[nombre_limpio] = float(rm_estimado)
            except (ValueError, TypeError, InvalidOperation):
                continue
    except Exception:
        maximos_actuales = {'press_banca': 80.0, 'sentadilla': 100.0}

    # --- PASO 2: Crear perfil y generar plan con el planificador correcto ---
    perfil = crear_perfil_desde_cliente(cliente)
    perfil.maximos_actuales = maximos_actuales

    # ¡Usamos el PlanificadorHelms que ya hemos corregido!
    planificador = PlanificadorHelms(perfil)
    plan_completo = planificador.generar_plan_anual()

    # --- PASO 3: Preparar el contexto para la plantilla ---
    plan_por_bloques = plan_completo.get('plan_por_bloques', [])

    # Calcular el total de semanas sumando la duración de cada bloque
    total_semanas = sum(bloque.get('duracion', 0) for bloque in plan_por_bloques)

    context = {
        'cliente': cliente,
        'plan_por_bloques': plan_por_bloques,
        'total_semanas': total_semanas  # Ahora esto debería ser 52
    }

    return render(request, 'entrenos/vista_resumen_anual.html', context)
