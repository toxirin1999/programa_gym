# Archivo: entrenos/views_liftin_adicionales.py - VISTAS ADICIONALES PARA LIFTIN
from rutinas.models import Rutina, Programa
from .forms import ImportarLiftinCompletoForm

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

from django.utils import timezone


@login_required
def importar_liftin_completo(request):
    """
    Vista para importar entrenamiento completo de Liftin con todos los campos
    """
    if request.method == 'POST':
        form = ImportarLiftinCompletoForm(request.POST)
        formset = EjercicioLiftinFormSet(request.POST)

        from django.utils import timezone

        if form.is_valid() and formset.is_valid():
            # Crear primero el programa
            fecha = timezone.now().strftime('%Y-%m-%d')
            nombre_programa = f"Programa importado {fecha}"
            programa = Programa.objects.create(nombre=nombre_programa)

            # Ahora crear la rutina y asociarla al programa
            nombre_rutina = f"Rutina Liftin {fecha}"
            rutina = Rutina.objects.create(nombre=nombre_rutina, programa=programa)

            # Asociar rutina al entrenamiento
            entrenamiento = form.save(commit=False)
            entrenamiento.rutina = rutina
            entrenamiento.save()

            # Guardar ejercicios
            ejercicios_guardados = 0
            for ejercicio_form in formset:
                if ejercicio_form.cleaned_data and not ejercicio_form.cleaned_data.get('DELETE', False):
                    ejercicio = ejercicio_form.save(commit=False)
                    ejercicio.entreno = entrenamiento
                    ejercicio.save()
                    ejercicios_guardados += 1

            messages.success(
                request,
                f'✅ Entrenamiento de Liftin importado exitosamente con {ejercicios_guardados} ejercicios!'
            )
            return redirect('entrenos:dashboard_liftin')

        else:
            messages.error(request, '❌ Error en el formulario. Revisa los datos ingresados.')
    else:
        form = ImportarLiftinCompletoForm()
        formset = EjercicioLiftinFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Importar Entrenamiento Completo de Liftin',
        'clientes': Cliente.objects.all().order_by('nombre'),
    }

    return render(request, 'entrenos/importar_liftin_completo.html', context)


@login_required
def importar_liftin_basico(request):
    """
    Vista para importación básica de Liftin (versión simplificada)
    """
    if request.method == 'POST':
        form = ImportarLiftinBasicoForm(request.POST)

        if form.is_valid():
            entrenamiento = form.save(commit=False)
            entrenamiento.rutina = rutina  # asignada manualmente
            entrenamiento.save()

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
