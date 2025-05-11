from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg
from .models import Cliente, Medida, RevisionProgreso
from .forms import ClienteForm, MedidaForm, RevisionProgresoForm
from django.contrib import messages
from collections import defaultdict
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from clientes.models import RevisionProgreso


# @login_required
def datos_graficas(request, cliente_id):
    registros = RevisionProgreso.objects.filter(cliente_id=cliente_id).order_by('fecha')

    fechas = [reg.fecha.strftime('%Y-%m-%d') for reg in registros]
    pesos = [reg.peso for reg in registros]
    grasas = [reg.grasa_corporal for reg in registros]
    cinturas = [reg.cintura for reg in registros]

    return JsonResponse({
        'fechas': fechas,
        'pesos': pesos,
        'grasas': grasas,
        'cinturas': cinturas
    })


def asignar_dieta_directo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteDietaForm(request.POST)
        if form.is_valid():
            cliente_dieta = form.save(commit=False)
            cliente_dieta.cliente = cliente
            cliente_dieta.save()
            messages.success(request, "Dieta asignada correctamente.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ClienteDietaForm()

    return render(request, 'dietas/asignar_dieta.html', {
        'form': form,
        'cliente': cliente
    })


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
    }

    return render(request, 'clientes/dashboard.html', context)


# Vista detalle cliente

def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    revisiones = cliente.revisiones.order_by('fecha')
    ultima_revision = revisiones.last()

    fechas = [rev.fecha.strftime("%d/%m/%Y") for rev in revisiones]
    pesos = [float(rev.peso_corporal or 0) for rev in revisiones]
    grasas = [float(rev.grasa_corporal or 0) for rev in revisiones]
    cinturas = [float(rev.cintura or 0) for rev in revisiones]

    return render(request, 'clientes/detalle.html', {
        'cliente': cliente,
        'ultima_revision': ultima_revision,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'grasas': json.dumps(grasas),
        'cinturas': json.dumps(cinturas),
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
    return render(request, 'clientes/index.html', {'clientes': clientes})


def asignar_programa_a_cliente(request, programa_id):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        programa = get_object_or_404(Programa, id=programa_id)
        cliente.programa = programa
        cliente.save()
        return redirect('detalle_programa', programa_id=programa_id)
