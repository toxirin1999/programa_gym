from datetime import date

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from clientes.models import Cliente
from .models import Dieta, ClienteDieta
from .forms import DietaForm, ClienteDietaForm, ComidaForm
from reportlab.pdfgen import canvas


def quitar_dieta(request, cliente_dieta_id):
    cliente_dieta = get_object_or_404(ClienteDieta, id=cliente_dieta_id)
    if request.method == 'POST':
        cliente_dieta.delete()
        messages.success(request, "Dieta desasignada correctamente.")
        return redirect('listar_dietas')
    return render(request, 'dietas/quitar_dieta.html', {'cliente_dieta': cliente_dieta})


def listar_dietas(request):
    dietas = Dieta.objects.all()
    clientes = Cliente.objects.all()
    cliente_activo_id = request.GET.get('cliente_id')
    cliente_dietas = ClienteDieta.objects.select_related('cliente', 'dieta')

    if cliente_activo_id:
        cliente_activo_id = int(cliente_activo_id)
        asignadas = ClienteDieta.objects.filter(cliente_id=cliente_activo_id).values_list('dieta_id', flat=True)
        asignadas_dict = set(asignadas)
    else:
        cliente_activo_id = None
        asignadas_dict = set()

    return render(request, 'dietas/listar_dietas.html', {
        'dietas': dietas,
        'clientes': clientes,
        'cliente_activo_id': cliente_activo_id,
        'asignadas_dict': asignadas_dict,
        'cliente_dietas': cliente_dietas,
    })


def ver_dieta(request, dieta_id):
    dieta = get_object_or_404(Dieta, id=dieta_id)
    cliente_dietas = ClienteDieta.objects.filter(dieta=dieta).select_related('cliente')
    comidas = dieta.comidas.all()
    return render(request, 'dietas/ver_dieta.html', {
        'dieta': dieta,
        'comidas': comidas,
        'clientes': Cliente.objects.all(),  # Para el selector del modal
        'cliente_dietas': cliente_dietas  # Lista de asignaciones
    })


def agregar_dieta(request):
    if request.method == 'POST':
        form = DietaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_dietas')
    else:
        form = DietaForm()
    return render(request, 'dietas/agregar_dieta.html', {'form': form})


def editar_dieta(request, dieta_id):
    dieta = get_object_or_404(Dieta, id=dieta_id)
    if request.method == 'POST':
        form = DietaForm(request.POST, instance=dieta)
        if form.is_valid():
            form.save()
            messages.success(request, "La dieta fue actualizada correctamente.")
            return redirect('ver_dieta', dieta_id=dieta.id)
    else:
        form = DietaForm(instance=dieta)
    return render(request, 'dietas/editar_dieta.html', {'form': form, 'dieta': dieta})


def eliminar_dieta(request, dieta_id):
    dieta = get_object_or_404(Dieta, id=dieta_id)
    if request.method == 'POST':
        dieta.delete()
        messages.success(request, "La dieta fue eliminada.")
        return redirect('listar_dietas')
    return render(request, 'dietas/eliminar_dieta.html', {'dieta': dieta})


def asignar_dieta(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        dieta_id = request.POST.get('dieta_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        dieta = get_object_or_404(Dieta, id=dieta_id)
        ClienteDieta.objects.create(cliente=cliente, dieta=dieta, fecha_inicio=date.today())
        messages.success(request, f"La dieta '{dieta.nombre}' fue asignada a {cliente.nombre} correctamente.")
        return redirect('listar_dietas')


from django.utils import timezone


def asignar_dieta_ajax(request):
    if request.method == 'POST':
        dieta_id = request.POST.get('dieta_id')
        cliente_id = request.POST.get('cliente_id')

        dieta = get_object_or_404(Dieta, id=dieta_id)
        cliente = get_object_or_404(Cliente, id=cliente_id)

        # ✅ Cerrar asignaciones anteriores con fecha_fin
        ClienteDieta.objects.filter(cliente=cliente, fecha_fin__isnull=True).update(fecha_fin=timezone.now())

        # ✅ Crear nueva asignación activa
        ClienteDieta.objects.create(
            cliente=cliente,
            dieta=dieta,
            fecha_inicio=timezone.now()
        )

        return JsonResponse({'success': True, 'message': 'Dieta asignada correctamente.'})
    return JsonResponse({'success': False, 'message': 'Solicitud inválida.'})


def exportar_dieta_pdf(request, dieta_id):
    dieta = get_object_or_404(Dieta, id=dieta_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{dieta.nombre}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 14)
    p.drawString(100, 800, f"Dieta: {dieta.nombre}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Calorías: {dieta.calorias_totales}")
    p.drawString(100, 760, f"Descripción: {dieta.descripcion}")

    y = 740
    for comida in dieta.comidas.all():
        p.drawString(100, y, f"{comida.hora_aproximada} - {comida.nombre}: {comida.descripcion}")
        y -= 20

    p.showPage()
    p.save()
    return response


def agregar_comida(request, dieta_id):
    dieta = get_object_or_404(Dieta, id=dieta_id)
    if request.method == 'POST':
        form = ComidaForm(request.POST)
        if form.is_valid():
            comida = form.save(commit=False)
            comida.dieta = dieta
            comida.save()
            messages.success(request, 'Comida añadida correctamente.')
            return redirect('ver_dieta', dieta_id=dieta.id)
    else:
        form = ComidaForm()

    return render(request, 'dietas/agregar_comida.html', {
        'dieta': dieta,
        'form': form
    })


def asignar_dieta_directo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteDietaForm(request.POST)
        if form.is_valid():
            cliente_dieta = form.save(commit=False)
            cliente_dieta.cliente = cliente
            cliente_dieta.save()
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ClienteDietaForm()
    return render(request, 'clientes/asignar_dieta.html', {'form': form, 'cliente': cliente})
