from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg
from .models import Cliente, Medida, RevisionProgreso
from .forms import ClienteForm, MedidaForm, RevisionProgresoForm
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import Count
from entrenos.models import EntrenoRealizado
from datetime import date, timedelta
from .forms import ObjetivoClienteForm
from .models import ObjetivoCliente
from datetime import timedelta, date
from django.db.models import F
from .models import RevisionProgreso  # o como se llame tu modelo de revisiones
from datetime import date
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Programa
from collections import defaultdict
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from clientes.models import RevisionProgreso
from entrenos.models import EntrenoRealizado

from django.http import JsonResponse
from .forms import DietaAsignadaForm
from django.db.models import Q

from entrenos.models import EntrenoRealizado
from collections import defaultdict
from datetime import timedelta
import json
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import now
from datetime import timedelta

from django.http import HttpResponse
from .models import Cliente


def exportar_historial(request, cliente_id):
    cliente = Cliente.objects.get(pk=cliente_id)
    # Aquí puedes generar PDF o Excel, por ahora solo devolvemos texto
    return HttpResponse(f"Exportando historial de {cliente.nombre}")


def historial_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    historial = EntrenoRealizado.objects.filter(cliente=cliente).prefetch_related('detalles__ejercicio').order_by(
        '-fecha')

    # Agrupar por semana
    historial_semanal = defaultdict(list)
    for entreno in historial:
        lunes = entreno.fecha - timedelta(days=entreno.fecha.weekday())
        historial_semanal[lunes].append(entreno)
    historial_semanal = dict(sorted(historial_semanal.items(), reverse=True))

    # Estadísticas
    total_entrenos = historial.count()
    total_semanas = len(historial_semanal)
    promedio_semanal = Decimal(total_entrenos / total_semanas).quantize(Decimal("0.1"),
                                                                        rounding=ROUND_HALF_UP) if total_semanas else Decimal(
        "0.0")

    # Datos para gráficos
    labels = []
    entrenos_por_semana = []
    volumen_por_semana = []

    for semana, entrenos in historial_semanal.items():
        labels.append(semana.strftime('%d %b'))
        entrenos_por_semana.append(len(entrenos))
        volumen = sum(d.series * d.repeticiones * float(d.peso_kg) for e in entrenos for d in e.detalles.all())
        volumen_por_semana.append(round(volumen, 2))

    grafico_data = {
        'labels': labels,
        'entrenos': entrenos_por_semana,
        'volumen': volumen_por_semana
    }

    return render(request, 'clientes/historial.html', {
        'cliente': cliente,
        'historial_semanal': historial_semanal,
        'total_entrenos': total_entrenos,
        'promedio_semanal': promedio_semanal,
        'grafico_data': json.dumps(grafico_data),
    })


def eliminar_revision(request, revision_id):
    revision = get_object_or_404(RevisionProgreso, id=revision_id)
    cliente_id = revision.cliente.id
    revision.delete()
    return redirect('lista_revisiones', cliente_id=cliente_id)


def eliminar_objetivo(request, pk):
    objetivo = get_object_or_404(ObjetivoCliente, pk=pk)
    cliente_id = objetivo.cliente.id
    objetivo.delete()
    messages.success(request, "Objetivo eliminado.")
    return redirect('detalle_cliente', cliente_id=cliente_id)


def editar_objetivo(request, pk):
    objetivo = get_object_or_404(ObjetivoCliente, pk=pk)
    cliente = objetivo.cliente

    if request.method == 'POST':
        form = ObjetivoClienteForm(request.POST, instance=objetivo, cliente=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Objetivo actualizado.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ObjetivoClienteForm(request.POST, instance=objetivo, cliente=cliente)

    return render(request, 'clientes/definir_objetivo.html', {
        'form': form,
        'cliente': cliente,
        'editar': True
    })


def definir_objetivo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ObjetivoClienteForm(request.POST, cliente=cliente)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.cliente = cliente
            objetivo.save()
            messages.success(request, "Objetivo guardado.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ObjetivoClienteForm()

    return render(request, 'clientes/definir_objetivo.html', {
        'form': form,
        'cliente': cliente
    })


@require_GET
def datos_comparacion(request):
    ids = request.GET.getlist('ids[]')
    medida = request.GET.get('medida', 'peso')

    campo_map = {
        'peso': 'peso_corporal',
        'grasa': 'grasa_corporal',
        'cintura': 'cintura',
    }

    campo = campo_map.get(medida, 'peso_corporal')
    data = []

    for cliente_id in ids:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')
        fechas = [rev.fecha.strftime('%Y-%m-%d') for rev in revisiones]
        valores = [getattr(rev, campo) for rev in revisiones]
        data.append({
            'nombre': cliente.nombre,
            'fechas': fechas,
            'valores': valores,
        })

    return JsonResponse(data, safe=False)


def comparar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/comparar.html', {'clientes': clientes})


@require_GET
def datos_graficas(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')

    start = request.GET.get('start')
    end = request.GET.get('end')
    if start and end:
        revisiones = revisiones.filter(fecha__range=[start, end])

    fechas = [rev.fecha.strftime('%Y-%m-%d') for rev in revisiones]

    data = {
        'fechas': fechas,
        'pesos': [rev.peso_corporal for rev in revisiones],
        'grasas': [rev.grasa_corporal for rev in revisiones],
        'cinturas': [rev.cintura for rev in revisiones],
        'pechos': [rev.pecho for rev in revisiones],
        'biceps': [rev.biceps for rev in revisiones],
        'muslos': [rev.muslos for rev in revisiones],
    }

    return JsonResponse(data)


def asignar_dieta_directo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = DietaAsignadaForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.cliente = cliente
            asignacion.save()
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = DietaAsignadaForm()

    return render(request, 'clientes/asignar_dieta.html', {'form': form, 'cliente': cliente})


def lista_revisiones(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    revisiones = cliente.revisiones.order_by('fecha')

    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if start_date and end_date:
        revisiones = revisiones.filter(fecha__range=[start_date, end_date])

    fechas = [r.fecha.strftime('%Y-%m-%d') for r in revisiones]
    pesos = [float(r.peso_corporal) if r.peso_corporal is not None else None for r in revisiones]
    grasas = [float(r.grasa_corporal) if r.grasa_corporal is not None else None for r in revisiones]

    alerts = [r.check_alerts() for r in revisiones if r.check_alerts()]

    context = {
        'cliente': cliente,
        'revisiones': revisiones,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'grasas': json.dumps(grasas),
        'alerts': alerts,
    }
    return render(request, 'clientes/lista_revisiones.html', context)


def agregar_revision(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = RevisionProgresoForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.cliente = cliente
            revision.save()
            return redirect('lista_revisiones', cliente_id=cliente.id)
    else:
        form = RevisionProgresoForm()
    return render(request, 'clientes/agregar_revision.html', {'form': form, 'cliente': cliente})


# Vista para listar medidas
def lista_medidas(request):
    medidas = Medida.objects.all()
    return render(request, 'list.html', {'medidas': medidas})


# Vista para agregar medida
def agregar_medida(request):
    if request.method == 'POST':
        form = MedidaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_medidas')
    else:
        form = MedidaForm()
    return render(request, 'form.html', {'form': form, 'titulo': 'Agregar Medida', 'volver_url': 'lista_medidas'})


# Vista principal de clientes (con programa)
def lista_clientes(request):
    clientes = Cliente.objects.select_related('programa').all()
    programas = Programa.objects.all()

    # Obtener parámetros del filtro desde la URL
    nombre = request.GET.get('nombre', '')
    programa_id = request.GET.get('programa', '')
    genero = request.GET.get('genero', '')

    # Aplicar filtros si vienen en la petición
    if nombre:
        clientes = clientes.filter(nombre__icontains=nombre)
    if programa_id:
        clientes = clientes.filter(programa_id=programa_id)
    if genero:
        clientes = clientes.filter(genero=genero)

    return render(request, 'list.html', {
        'titulo': 'Lista de Clientes',
        'objetos': clientes,
        'programas': programas,  # ✅ pasa los programas al template
        'encabezados': ['ID', 'Nombre', 'Email', 'Teléfono', 'Programa'],
        'campos': ['id', 'nombre', 'email', 'telefono', 'programa'],
        'agregar_url': 'agregar_cliente',
        'editar_url': 'editar_cliente',
        'eliminar_url': 'eliminar_cliente',
        'detalle_url': 'detalle_cliente',
    })


# Dashboard de clientes


def dashboard(request):
    clientes = Cliente.objects.all()
    total_clientes = clientes.count()
    total_revisiones = sum(cliente.revisiones.count() for cliente in clientes)

    # Promedios
    promedio_peso = 0
    promedio_grasa = 0
    total_mediciones = 0

    for cliente in clientes:
        ultima = cliente.revisiones.order_by('-fecha').first()
        if ultima:
            print(f"{cliente.nombre} ({ultima.fecha}) → {ultima.check_alerts()}")
        for rev in cliente.revisiones.all():
            if rev.peso_corporal:
                promedio_peso += rev.peso_corporal
            if rev.grasa_corporal:
                promedio_grasa += rev.grasa_corporal
            total_mediciones += 1

    if total_mediciones > 0:
        promedio_peso /= total_mediciones
        promedio_grasa /= total_mediciones
        # 📊 Datos de entrenos
    from datetime import date, timedelta
    from django.db.models.functions import TruncWeek, TruncMonth, TruncYear

    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)

    entrenos_hoy = EntrenoRealizado.objects.filter(fecha=hoy).count()
    entrenos_semana = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).count()
    entrenos_mes = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).count()
    entrenos_anio = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).count()
    entrenos_total = EntrenoRealizado.objects.count()

    semanas = EntrenoRealizado.objects.annotate(semana=TruncWeek('fecha')).values('semana').distinct().count()
    meses = EntrenoRealizado.objects.annotate(mes=TruncMonth('fecha')).values('mes').distinct().count()
    anios = EntrenoRealizado.objects.annotate(anio=TruncYear('fecha')).values('anio').distinct().count()

    promedio_semanal = round(entrenos_total / semanas, 1) if semanas else 0
    promedio_mensual = round(entrenos_total / meses, 1) if meses else 0
    promedio_anual = round(entrenos_total / anios, 1) if anios else 0

    # Agrupación de alertas
    from collections import defaultdict
    alertas_raw = defaultdict(list)

    for cliente in clientes:
        ultima = cliente.revisiones.order_by('-fecha').first()
        if ultima:
            alertas = ultima.check_alerts()
            if alertas:
                for alerta in alertas:
                    alertas_raw[alerta].append((cliente, ultima.fecha))

    # Convertimos el defaultdict a dict plano
    alertas_por_tipo = dict(alertas_raw)

    context = {'alertas_por_tipo': alertas_por_tipo, }

    # Datos adicionales
    resumen_programa = Cliente.objects.values('programa__nombre').annotate(count=Count('id'))
    genero_count = Cliente.objects.values('genero').annotate(count=Count('id'))
    peso_por_genero = Cliente.objects.values('genero').annotate(avg_peso=Avg('peso_corporal'))
    registro_por_mes = (
        Cliente.objects
        .extra(select={'month': "strftime('%%m', fecha_registro)"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    top_peso = Cliente.objects.order_by('-peso_corporal')[:5]
    color_por_alerta = {
        "Grasa corporal alta": "danger",
        "Peso corporal muy bajo": "warning",
        # Puedes agregar más tipos aquí
    }
    alertas_por_tipo_coloreadas = []
    for tipo, clientes_lista in alertas_por_tipo.items():
        alertas_por_tipo_coloreadas.append({
            'tipo': tipo,
            'color': color_por_alerta.get(tipo, 'secondary'),
            'clientes': clientes_lista
        })
        hoy = date.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        entrenos_hoy_lista = EntrenoRealizado.objects.filter(fecha=hoy).select_related('cliente', 'rutina')
        entrenos_semana_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).select_related('cliente',
                                                                                                         'rutina')
        entrenos_mes_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).select_related('cliente', 'rutina')
        entrenos_anio_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).select_related('cliente',
                                                                                                     'rutina')
        entrenos_todos_lista = EntrenoRealizado.objects.all().select_related('cliente', 'rutina')
    context = {
        'total_clientes': total_clientes,
        'total_revisiones': total_revisiones,
        'promedio_peso': round(promedio_peso, 1),
        'promedio_grasa': round(promedio_grasa, 1),
        'alertas_por_tipo': alertas_por_tipo,
        'total_alertas': sum(len(lst) for lst in alertas_por_tipo.values()),
        'resumen_programa': resumen_programa,
        'genero_count': list(genero_count),
        'peso_por_genero': list(peso_por_genero),
        'registro_por_mes': list(registro_por_mes),
        'alertas_por_tipo': dict(alertas_raw),
        'alertas_por_tipo_coloreadas': alertas_por_tipo_coloreadas,
        'color_por_alerta': color_por_alerta,
        'top_peso': top_peso,
        'entr_hoy': entrenos_hoy,
        'entr_semana': entrenos_semana,
        'entr_mes': entrenos_mes,
        'entr_anio': entrenos_anio,
        'entr_total': entrenos_total,
        'prom_sem': promedio_semanal,
        'prom_mes': promedio_mensual,
        'prom_anio': promedio_anual,
        'entr_hoy_lista': entrenos_hoy_lista,
        'entr_semana_lista': entrenos_semana_lista,
        'entr_mes_lista': entrenos_mes_lista,
        'entr_anio_lista': entrenos_anio_lista,
        'entr_todos_lista': entrenos_todos_lista,
    }

    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)

    entrenos_hoy_lista = EntrenoRealizado.objects.filter(fecha=hoy).select_related('cliente', 'rutina')
    entrenos_semana_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).select_related('cliente',
                                                                                                     'rutina')
    entrenos_mes_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).select_related('cliente', 'rutina')
    entrenos_anio_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).select_related('cliente', 'rutina')
    entrenos_todos_lista = EntrenoRealizado.objects.all().select_related('cliente', 'rutina')
    return render(request, 'clientes/dashboard.html', context)


# Vista detalle cliente

def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    revisiones = cliente.revisiones.order_by('fecha')
    ultima_revision = revisiones.last()
    historial = EntrenoRealizado.objects.filter(cliente=cliente).prefetch_related('detalles__ejercicio').order_by(
        '-fecha')

    historial_semanal = defaultdict(list)
    # Prepara datos para Chart.js
    labels = []
    entrenos_por_semana = []
    volumen_por_semana = []

    for semana_inicio, entrenos in historial_semanal.items():
        label = f"{semana_inicio.strftime('%d %b')}"
        labels.append(label)
        entrenos_por_semana.append(len(entrenos))

        volumen = 0
        for entreno in entrenos:
            for detalle in entreno.detalles.all():
                volumen += detalle.series * detalle.repeticiones * float(detalle.peso_kg)
        volumen_por_semana.append(round(volumen, 2))

    # Serializar para JS
    grafico_data = {
        'labels': labels,
        'entrenos': entrenos_por_semana,
        'volumen': volumen_por_semana,
    }
    from decimal import Decimal, ROUND_HALF_UP

    # total entrenos
    total_entrenos = historial.count()
    total_semanas = len(historial_semanal)

    # evitar división por 0
    if total_semanas > 0:
        promedio_semanal = Decimal(total_entrenos / total_semanas).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    else:
        promedio_semanal = Decimal("0.0")
    for entreno in historial:
        lunes = entreno.fecha - timedelta(days=entreno.fecha.weekday())  # inicio de semana
        historial_semanal[lunes].append(entreno)

    historial_semanal = dict(sorted(historial_semanal.items(), reverse=True))  # ordenar por semana

    fechas = [rev.fecha.strftime("%d/%m/%Y") for rev in revisiones]
    pesos = [float(rev.peso_corporal or 0) for rev in revisiones]
    grasas = [float(rev.grasa_corporal or 0) for rev in revisiones]
    cinturas = [float(rev.cintura or 0) for rev in revisiones]

    objetivos = cliente.objetivos.all()
    hoy = date.today()
    revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')

    def delta_peso(dias):
        desde = hoy - timedelta(days=dias)
        recientes = revisiones.filter(fecha__gte=desde)
        if recientes.count() >= 2:
            return round(recientes.last().peso_corporal - recientes.first().peso_corporal, 1)
        return 0

    peso_7d = delta_peso(7)
    peso_30d = delta_peso(30)
    peso_90d = delta_peso(90)

    peso_total = 0
    if revisiones.count() >= 2:
        peso_total = round(revisiones.last().peso_corporal - revisiones.first().peso_corporal, 1)
    return render(request, 'clientes/detalle.html', {
        'cliente': cliente,
        'ultima_revision': ultima_revision,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'grasas': json.dumps(grasas),
        'cinturas': json.dumps(cinturas),
        'objetivos': objetivos,
        'cliente': cliente,
        'today': date.today(),
        'peso_7d': peso_7d,
        'peso_30d': peso_30d,
        'peso_90d': peso_90d,
        'historial_semanal': historial_semanal,
        'total_entrenos': total_entrenos,
        'promedio_semanal': promedio_semanal,
        'grafico_data': json.dumps(grafico_data),
        'peso_total': peso_total,
    })


# Vista agregar cliente
def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('clientes_index')
    else:
        form = ClienteForm()
    return render(request, 'clientes/agregar.html', {
        'form': form,
        'titulo': 'Agregar Cliente',
        'volver_url': 'clientes_index',
    })


# Vista editar cliente
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('clientes_index')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/editar.html', {'form': form, 'cliente': cliente})


# Vista eliminar cliente
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes_index')
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})


# Vista home
def home(request):
    return render(request, 'clientes/home.html')


# Vista index
def index(request):
    clientes = Cliente.objects.all()
    for cliente in clientes:
        cliente.ultima_revision = cliente.revisiones.order_by('-fecha').first()

    programas = Programa.objects.all()

    return render(request, 'clientes/index.html', {
        'clientes': clientes,
        'programas': programas,
        'today': date.today(),
    })


def asignar_programa_a_cliente(request, programa_id):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        programa = get_object_or_404(Programa, id=programa_id)
        cliente.programa = programa
        cliente.save()
        return redirect('detalle_programa', programa_id=programa_id)


def actualizar_recordatorio_peso(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    fecha = request.POST.get("proximo_registro_peso")
    if fecha:
        cliente.proximo_registro_peso = fecha
        cliente.save()
    return HttpResponseRedirect(reverse("detalle_cliente", args=[cliente.id]))
