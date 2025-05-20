from datetime import date, timedelta
from decimal import Decimal
import copy
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django import forms
from django.db.models import Avg, Sum

from rutinas.models import Rutina, RutinaEjercicio, Ejercicio
from clientes.models import Cliente
from .models import EntrenoRealizado, SerieRealizada, PlanPersonalizado
from .forms import SeleccionClienteForm, DetalleEjercicioForm, FiltroClienteForm


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
    from django.core.paginator import Paginator  # Importación añadida

    form = FiltroClienteForm(request.GET or None)
    entrenos = EntrenoRealizado.objects.select_related('cliente', 'rutina').prefetch_related('series__ejercicio')

    if form.is_valid() and form.cleaned_data['cliente']:
        cliente = form.cleaned_data['cliente']
        entrenos = entrenos.filter(cliente=cliente)
    else:
        cliente = None

    entrenos = entrenos.order_by('-fecha')

    # Implementación de paginación
    paginator = Paginator(entrenos, 10)  # 10 entrenamientos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'entrenos/historial_entrenos.html', {
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


def adaptar_plan_personalizado(entreno, ejercicios_forms, cliente, rutina):
    """
    Adapta el plan personalizado del cliente basado en su rendimiento.
    """
    # Obtener el cliente directamente de la base de datos usando el ID del entreno
    try:
        from clientes.models import Cliente
        cliente_real = Cliente.objects.get(id=entreno.cliente_id)
        print(f"Cliente obtenido de entreno: {cliente_real.id} - {cliente_real.nombre}")
    except Exception as e:
        print(f"❌ Error al obtener cliente desde entreno: {str(e)}")
        return

    # Validar rutina
    if not isinstance(rutina, Rutina):
        try:
            if isinstance(rutina, int) or (isinstance(rutina, str) and rutina.isdigit()):
                rutina_id = int(rutina)
                rutina = Rutina.objects.get(id=rutina_id)
            else:
                print(f"❌ Tipo de rutina no válido: {type(rutina)}")
                return
        except Exception as e:
            print(f"❌ Error al obtener rutina: {str(e)}")
            return

    print(f"✅ Cliente validado: {cliente_real.id} - {cliente_real.nombre}")
    print(f"✅ Rutina validada: {rutina.id} - {rutina.nombre}")

    for ejercicio, _ in ejercicios_forms:
        try:
            # Validar ejercicio
            if not isinstance(ejercicio, Ejercicio):
                try:
                    if isinstance(ejercicio, int) or (isinstance(ejercicio, str) and ejercicio.isdigit()):
                        ejercicio_id = int(ejercicio)
                        ejercicio = Ejercicio.objects.get(id=ejercicio_id)
                    else:
                        ejercicio = Ejercicio.objects.get(nombre=ejercicio)
                except Exception as e:
                    print(f"❌ Error al obtener ejercicio: {str(e)}")
                    continue

            print(f"✅ Ejercicio validado: {ejercicio.id} - {ejercicio.nombre}")

            # Obtener plan existente y asignación
            plan_existente = PlanPersonalizado.objects.filter(
                cliente_id=cliente_real.id,
                ejercicio_id=ejercicio.id,
                rutina_id=rutina.id
            ).first()

            asignacion = RutinaEjercicio.objects.filter(
                rutina_id=rutina.id,
                ejercicio_id=ejercicio.id
            ).first()

            if not asignacion:
                print(f"❌ No se encontró asignación para {ejercicio.nombre} en {rutina.nombre}")
                continue

            reps_objetivo = plan_existente.repeticiones_objetivo if plan_existente else asignacion.repeticiones

            # Verificar series completadas
            series = SerieRealizada.objects.filter(
                entreno_id=entreno.id,
                ejercicio_id=ejercicio.id
            )
            total_series = series.count()

            if total_series == 0:
                print(f"❌ No hay series para {ejercicio.nombre}")
                continue

            # Condición más flexible para incremento
            series_completadas = sum(1 for s in series if s.completado)
            porcentaje_completado = series_completadas / total_series

            series_con_reps_cercanas = sum(
                1 for s in series
                if abs(s.repeticiones - reps_objetivo) <= 1
            )
            porcentaje_reps_cercanas = series_con_reps_cercanas / total_series

            print(f"Series completadas: {series_completadas}/{total_series} ({porcentaje_completado:.0%})")
            print(
                f"Series con reps cercanas: {series_con_reps_cercanas}/{total_series} ({porcentaje_reps_cercanas:.0%})")

            series_exitosas = porcentaje_completado >= 0.75 and porcentaje_reps_cercanas >= 0.75

            if series_exitosas:
                print(f"✅ Incrementando peso para {ejercicio.nombre}")
                total_peso = series.aggregate(Sum('peso_kg'))['peso_kg__sum'] or 0
                promedio_peso = total_peso / total_series
                nuevo_peso = round(promedio_peso * Decimal("1.10"), 1)

                print(f"Peso actual: {promedio_peso}, Nuevo peso: {nuevo_peso}")

                # Usar el ORM de Django en lugar de SQL directo
                try:
                    # Reemplaza la parte de guardar el plan con este código:
                    try:
                        # Usar raw SQL para actualizar o insertar
                        from django.db import connection

                        # Verificar si existe el plan
                        plan_exists = PlanPersonalizado.objects.filter(
                            cliente_id=cliente_real.id,
                            ejercicio_id=ejercicio.id,
                            rutina_id=rutina.id
                        ).exists()

                        if plan_exists:
                            # Actualizar usando raw SQL
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """
                                    UPDATE entrenos_planpersonalizado 
                                    SET repeticiones_objetivo = ?, peso_objetivo = ? 
                                    WHERE cliente_id = ? AND ejercicio_id = ? AND rutina_id = ?
                                    """,
                                    [int(reps_objetivo), float(nuevo_peso), int(cliente_real.id), int(ejercicio.id),
                                     int(rutina.id)]
                                )
                            print(f"Plan actualizado mediante SQL raw: {nuevo_peso} kg")
                        else:
                            # Insertar usando raw SQL
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """
                                    INSERT INTO entrenos_planpersonalizado 
                                    (cliente_id, ejercicio_id, rutina_id, repeticiones_objetivo, peso_objetivo) 
                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    [int(cliente_real.id), int(ejercicio.id), int(rutina.id), int(reps_objetivo),
                                     float(nuevo_peso)]
                                )
                            print(f"Plan creado mediante SQL raw: {nuevo_peso} kg")
                    except Exception as e:
                        print(f"❌ Error al guardar plan mediante SQL raw: {str(e)}")

                except Exception as e:
                    print(f"❌ Error al guardar plan mediante ORM: {str(e)}")
            else:
                print(f"❌ No se incrementa peso para {ejercicio.nombre} - No cumple criterios")
        except Exception as e:
            print(f"Error al adaptar plan para {ejercicio.nombre}: {str(e)}")


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
    Maneja la creación de un nuevo entrenamiento.

    Args:
        request: Objeto HttpRequest
        rutina_id: ID de la rutina

    Returns:
        HttpResponse con la plantilla renderizada
    """
    rutina = get_object_or_404(Rutina.objects.prefetch_related('rutinaejercicio_set__ejercicio'), id=rutina_id)
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

    if request.method == 'POST':
        cliente_form = SeleccionClienteForm(request.POST)
        ejercicios_validos = True

        for asignacion in rutina.rutinaejercicio_set.select_related('ejercicio'):
            ejercicio = asignacion.ejercicio  # Eliminado copy.copy innecesario
            form = DetalleEjercicioForm(request.POST, prefix=str(ejercicio.id))
            ejercicios_forms.append((ejercicio, form))

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

            # Crear series realizadas
            crear_entreno(entreno, ejercicios_forms, request, cliente, rutina)

            # Adaptar plan personalizado
            adaptar_plan_personalizado(entreno, ejercicios_forms, cliente, rutina)

            # Actualizar rutina del cliente
            exito, mensaje = actualizar_rutina_cliente(cliente, rutina)

            # Mostrar mensaje de éxito
            messages.success(request, "✅ Entreno guardado con éxito.")
            if exito:
                messages.success(request, mensaje)
            else:
                messages.warning(request, mensaje)

            return redirect('hacer_entreno')
    else:
        cliente_form = SeleccionClienteForm(initial={'cliente': cliente_inicial})

        if cliente_form is not None:
            cliente_form.fields['cliente'].widget = forms.HiddenInput()

        # Obtener datos previos si hay cliente inicial
        if cliente_inicial:
            ultimo_entreno = (
                EntrenoRealizado.objects
                .filter(cliente=cliente_inicial, rutina=rutina)
                .order_by('-id')
                .prefetch_related('series__ejercicio')
                .first()
            )
            if ultimo_entreno:
                for serie in ultimo_entreno.series.all():
                    datos_previos.setdefault(serie.ejercicio.id, []).append({
                        'repeticiones': serie.repeticiones,
                        'peso_kg': serie.peso_kg
                    })

    # Preparar formularios para cada ejercicio
    for asignacion in rutina.rutinaejercicio_set.select_related('ejercicio'):
        ejercicio = asignacion.ejercicio  # Eliminado copy.copy innecesario
        previas = datos_previos.get(ejercicio.id, [])

        plan = None
        if isinstance(cliente_inicial, Cliente):
            # Usar IDs en lugar de objetos para evitar problemas de tipo
            plan = PlanPersonalizado.objects.filter(
                cliente_id=cliente_inicial.id,
                ejercicio_id=ejercicio.id,
                rutina_id=rutina.id
            ).first()

        if plan:
            reps_plan = plan.repeticiones_objetivo
            peso_plan = plan.peso_objetivo
            adaptado = True
        else:
            reps_plan = asignacion.repeticiones
            peso_plan = asignacion.peso_kg
            adaptado = False

        initial_data = {
            'series': len(previas) if previas else asignacion.series,
            'repeticiones': previas[0]['repeticiones'] if previas else reps_plan,
            'peso_kg': previas[0]['peso_kg'] if previas else peso_plan,
            'completado': True,
            'ejercicio_id': ejercicio.id,
        }

        form = DetalleEjercicioForm(initial=initial_data, prefix=str(ejercicio.id))
        num_series = len(previas) if previas else asignacion.series
        ejercicio.series_datos = []

        for idx in range(num_series):
            serie_data = {
                'repeticiones': previas[idx]['repeticiones'] if idx < len(previas) else reps_plan,
                'peso_kg': previas[idx]['peso_kg'] if idx < len(previas) else peso_plan,
                'numero': idx + 1,
                'adaptado': adaptado,
                'peso_adaptado': adaptado
            }
            ejercicio.series_datos.append(serie_data)

        ejercicios_forms.append((ejercicio, form))

    # Renderizar plantilla (corregido el error de indentación)
    return render(request, 'entrenos/empezar_entreno.html', {
        'rutina': rutina,
        'cliente_form': cliente_form,
        'ejercicios_forms': ejercicios_forms,
        'cliente_inicial': cliente_inicial
    })
    series = SerieRealizada.objects.filter(entreno=entreno)
    print(f"Total series guardadas: {series.count()}")
    for s in series:
        print(f"Serie: {s.ejercicio.nombre}, #{s.serie_numero}, Reps: {s.repeticiones}, Completado: {s.completado}")


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
    Muestra los detalles de un entrenamiento anterior.

    Args:
        request: Objeto HttpRequest
        cliente_id: ID del cliente
        rutina_id: ID de la rutina

    Returns:
        HttpResponse con la plantilla renderizada
    """
    # Obtenemos el cliente y la rutina por ID
    cliente = get_object_or_404(Cliente, id=cliente_id)
    rutina = get_object_or_404(Rutina, id=rutina_id)

    # Último entreno realizado
    entreno_anterior = (
        EntrenoRealizado.objects
        .filter(cliente=cliente, rutina=rutina)
        .prefetch_related('series__ejercicio')
        .order_by('-fecha', '-id')
        .first()
    )

    # Plan personalizado o rutina original
    ejercicios_planificados = []
    for asignacion in rutina.rutinaejercicio_set.select_related('ejercicio'):
        ejercicio = asignacion.ejercicio

        # Usamos cliente_id directamente en lugar de cliente para evitar problemas de tipo
        plan = PlanPersonalizado.objects.filter(
            cliente_id=cliente_id,  # Usamos el ID en lugar del objeto
            ejercicio_id=ejercicio.id,  # Usamos el ID en lugar del objeto
            rutina_id=rutina_id  # Usamos el ID en lugar del objeto
        ).first()

        peso_base = asignacion.peso_kg
        peso_adaptado = False
        peso_objetivo = peso_base

        if plan and plan.peso_objetivo != peso_base:
            peso_objetivo = plan.peso_objetivo
            peso_adaptado = True

        ejercicios_planificados.append({
            'nombre': ejercicio.nombre,
            'series': asignacion.series,
            'repeticiones': asignacion.repeticiones,
            'peso_kg': peso_objetivo,
            'peso_adaptado': peso_adaptado,
            'peso_base': peso_base
        })

    return render(request, 'entrenos/entreno_anterior.html', {
        'cliente': cliente,
        'rutina': rutina,
        'entreno': entreno_anterior,
        'plan': ejercicios_planificados
    })
