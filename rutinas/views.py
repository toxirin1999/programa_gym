from django.shortcuts import render, get_object_or_404, redirect
from .forms import ProgramaForm, EjercicioForm, RutinaForm, RutinaEjercicioForm
from .models import Programa, Ejercicio, Rutina
from django.contrib import messages
from clientes.models import Cliente
from .models import RutinaEjercicio
from django.contrib import messages

import os
from django.conf import settings
from .models import Programa
from .forms import ProgramaForm
from django.shortcuts import render, get_object_or_404, redirect


def eliminar_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id)
    programa_id = rutina.programa.id  # guardamos el ID del programa para redirigir luego
    if request.method == 'POST':
        rutina.delete()
        return redirect('detalle_programa', programa_id=programa_id)
    return render(request, 'rutinas/eliminar_rutina.html', {'rutina': rutina})


def asignar_programa_a_cliente(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    clientes = Cliente.objects.all()

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.programa = programa
        cliente.save()
        messages.success(request, f'✅ Programa asignado correctamente a {cliente.nombre}')
        return redirect('detalle_programa', programa_id=programa.id)

    return render(request, 'clientes/asignar_programa.html', {'programa': programa, 'clientes': clientes})


def asignar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.programa = programa  # Asigna el programa al cliente
        cliente.save()
        messages.success(request, f'Programa "{programa.nombre}" asignado a {cliente.nombre} correctamente.')
        return redirect('detalle_programa', programa_id=programa.id)

    # Si alguien accede por GET, lo redirigimos al detalle del programa
    return redirect('detalle_programa', programa_id=programa.id)


def detalle_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    rutinas = Rutina.objects.filter(programa=programa)
    clientes = Cliente.objects.all()  # 👈 Aquí cargamos todos los clientes

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.programa = programa
        cliente.save()
        messages.success(request, f"Programa '{programa.nombre}' asignado a {cliente.nombre}")
        return redirect('programas/detalle_programa', programa_id=programa_id)

    return render(request, 'programas/detalle_programa.html', {
        'programa': programa,
        'rutinas': rutinas,
        'clientes': clientes,  # 👈 Lo pasamos al template
    })


def eliminar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    programa.delete()
    return redirect('lista_programas')  # asegúrate de que este nombre coincida con tu urls.py


from django.core.paginator import Paginator


def lista_programas(request):
    buscar = request.GET.get("buscar", "")
    programas = Programa.objects.all()
    if buscar:
        programas = programas.filter(nombre__icontains=buscar)

    paginator = Paginator(programas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "./programas/lista_programas.html", {"page_obj": page_obj})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Programa
from .forms import ProgramaForm


def agregar_programa(request):
    if request.method == 'POST':
        form = ProgramaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_programas')
    else:
        form = ProgramaForm()
    return render(request, 'programas/form_programa.html', {'form': form, 'titulo': 'Agregar Programa'})


def index(request):
    rutinas = Rutina.objects.all()
    return render(request, 'rutinas/index.html', {'rutinas': rutinas})


def lista_ejercicios(request):
    ejercicios = Ejercicio.objects.all()
    return render(request, 'rutinas/lista_ejercicios.html', {'ejercicios': ejercicios})


def agregar_ejercicio(request, rutina_id):
    rutina = get_object_or_404(Rutina, pk=rutina_id)
    if request.method == 'POST':
        form = RutinaEjercicioForm(request.POST)
        if form.is_valid():
            rutina_ejercicio = form.save(commit=False)
            rutina_ejercicio.rutina = rutina
            rutina_ejercicio.save()
            return redirect('detalle_rutina', rutina_id=rutina.id)
    else:
        form = RutinaEjercicioForm()
    return render(request, 'rutinas/agregar_ejercicio.html', {
        'form': form,
        'rutina': rutina,
    })


def agregar_rutina(request, programa_id):
    programa = get_object_or_404(Programa, pk=programa_id)
    rutina = None

    if request.method == 'POST':
        form = RutinaForm(request.POST)
        if form.is_valid():
            rutina = form.save(commit=False)
            rutina.programa = programa
            rutina.save()
            return redirect('detalle_programa', programa_id=programa.id)
    else:
        form = RutinaForm()

    return render(request, 'rutinas/agregar_rutina.html', {
        'form': form,
        'programa': programa,
        'rutina': rutina,  # pasamos rutina para el template
    })


def detalle_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, pk=rutina_id)
    ejercicios = rutina.ejercicios.all()  # Si hay relación M2M o FK

    return render(request, 'rutinas/detalle_rutina.html', {
        'rutina': rutina,
        'ejercicios': ejercicios,
    })


def agregar_rutina(request, programa_id):
    programa = get_object_or_404(Programa, pk=programa_id)
    if request.method == 'POST':
        form = RutinaForm(request.POST)
        if form.is_valid():
            rutina = form.save(commit=False)
            rutina.programa = programa
            rutina.save()
            form.save_m2m()  # Guarda la relación M2M ejercicios
            return redirect('detalle_programa', programa_id=programa.id)
    else:
        form = RutinaForm()
    return render(request, 'rutinas/agregar_rutina.html', {
        'form': form,
        'programa': programa,
    })


def editar_rutina_ejercicio(request, pk):
    ejercicio = get_object_or_404(RutinaEjercicio, pk=pk)

    if request.method == 'POST':
        form = RutinaEjercicioForm(request.POST, instance=ejercicio)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Cambios guardados correctamente.")
            return redirect('detalle_rutina', rutina_id=ejercicio.rutina.id)

    else:
        form = RutinaEjercicioForm(instance=ejercicio)

    return render(request, 'rutinas/editar_rutina_ejercicio.html', {
        'form': form,
        'ejercicio': ejercicio
    })


def eliminar_rutina_ejercicio(request, pk):
    ejercicio = get_object_or_404(RutinaEjercicio, pk=pk)
    # lógica para eliminar...


# rutinas/views.py

# ... tus imports existentes ...
from .forms import EjercicioForm  # Asegúrate de que esta importación exista
from .models import Ejercicio  # Asegúrate de que esta importación exista
from .models import Programa  # Mantener si lo usas en otras funciones


# ...

def agregar_ejercicio_general(request):
    # Esta vista es para agregar un NUEVO EJERCICIO general
    # No necesita un 'programa_id' ni un 'Programa' aquí.

    if request.method == 'POST':
        form = EjercicioForm(request.POST)  # <-- Usar EjercicioForm
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Ejercicio general agregado correctamente.')
            return redirect('lista_ejercicios')  # <-- Redirigir a la lista de ejercicios

    else:
        form = EjercicioForm()  # <-- Usar EjercicioForm

    return render(request, 'rutinas/agregar_ejercicio.html', {  # <-- Renderizar un template para Ejercicio
        'form': form,
        'titulo': 'Agregar Nuevo Ejercicio'
    })


def editar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    if request.method == 'POST':
        form = ProgramaForm(request.POST, instance=programa)
        if form.is_valid():
            form.save()
            return redirect('lista_programas')
    else:
        form = ProgramaForm(instance=programa)
    return render(request, 'programas/form_programa.html', {'form': form, 'titulo': 'Editar Programa'})


def eliminar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    if request.method == 'POST':
        programa.delete()
        messages.success(request, 'El programa ha sido eliminado correctamente.')
        return redirect('lista_programas')
    return render(request, 'programas/eliminar_programa.html', {'programa': programa})
