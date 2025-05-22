from datetime import date, timedelta
from collections import defaultdict
from django.core.serializers.json import DjangoJSONEncoder
import json
import copy
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
            adaptar_plan_personalizado(entreno, ejercicios_forms, cliente, rutina, request)

            # Actualizar rutina del cliente
            exito, mensaje = actualizar_rutina_cliente(cliente, rutina)

            # Mostrar mensaje de éxito
            messages.success(request, "✅ Entreno guardado con éxito.")
            if exito:
                messages.success(request, mensaje)
            else:
                messages.warning(request, mensaje)

            return redirect('resumen_entreno', entreno_id=entreno.id)
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
            fallos_anteriores = set()
            if ultimo_entreno:
                for serie in ultimo_entreno.series.all():
                    datos_previos.setdefault(serie.ejercicio.id, []).append({
                        'repeticiones': serie.repeticiones,
                        'peso_kg': serie.peso_kg
                    })
                for ejercicio in rutina.rutinaejercicio_set.select_related('ejercicio'):
                    series_previas = ultimo_entreno.series.filter(ejercicio=ejercicio.ejercicio)
                    total = series_previas.count()
                    completadas = sum(1 for s in series_previas if s.completado)
                    if total > 0 and completadas / total < 0.75:
                        fallos_anteriores.add(ejercicio.ejercicio.id)

    # Preparar formularios para cada ejercicio
    for asignacion in rutina.rutinaejercicio_set.select_related('ejercicio'):
        ejercicio = asignacion.ejercicio
        plan = None
        adaptado = False

        if isinstance(cliente_inicial, Cliente):
            plan = PlanPersonalizado.objects.filter(
                cliente_id=cliente_inicial.id,
                ejercicio_id=ejercicio.id,
                rutina_id=rutina.id
            ).first()

        if plan:
            reps_plan = plan.repeticiones_objetivo
            peso_plan = plan.peso_objetivo
            adaptado = True

            num_series = asignacion.series
            registro_fallos = 0
            session_key = f'adaptacion_{cliente_inicial.id}_{rutina.id}'
            if session_key in request.session:
                registro = request.session[session_key].get(str(ejercicio.id))
                if registro:
                    registro_fallos = registro.get('fallos_consecutivos', 0)
            ejercicio.series_datos = []

            for idx in range(num_series):
                ejercicio.series_datos.append({
                    'repeticiones': reps_plan,
                    'peso_kg': peso_plan,
                    'numero': idx + 1,
                    'adaptado': True,
                    'peso_adaptado': True,
                    'fallo_anterior': ejercicio.id in fallos_anteriores,
                    'fallos_consecutivos': registro_fallos
                })

        else:
            previas = datos_previos.get(ejercicio.id, [])
            reps_plan = asignacion.repeticiones
            peso_plan = asignacion.peso_kg

            num_series = len(previas) if previas else asignacion.series
            ejercicio.series_datos = []

            for idx in range(num_series):
                ejercicio.series_datos.append({
                    'repeticiones': previas[idx]['repeticiones'] if idx < len(previas) else reps_plan,
                    'peso_kg': previas[idx]['peso_kg'] if idx < len(previas) else peso_plan,
                    'numero': idx + 1,
                    'adaptado': False,
                    'peso_adaptado': False,
                    'fallo_anterior': ejercicio.id in fallos_anteriores,
                    'fallos_consecutivos': registro_fallos
                })

        initial_data = {
            'series': len(ejercicio.series_datos),
            'repeticiones': ejercicio.series_datos[0]['repeticiones'],
            'peso_kg': ejercicio.series_datos[0]['peso_kg'],
            'completado': True,
            'ejercicio_id': ejercicio.id,
        }

        form = DetalleEjercicioForm(initial=initial_data, prefix=str(ejercicio.id))
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


def resumen_entreno(request, entreno_id):
    """
    Muestra el resumen de un entrenamiento finalizado.

    Args:
        request: Objeto HttpRequest
        entreno_id: ID del entrenamiento recién creado

    Returns:
        HttpResponse con la plantilla renderizada
    """
    adaptaciones = request.session.pop('adaptaciones', [])  # Eliminamos al mostrar
    no_adaptados = request.session.pop('no_adaptados', [])
    adaptados_ids = [a['ejercicio_id'] for a in adaptaciones]
    no_adaptados_ids = [a['ejercicio_id'] for a in no_adaptados]
    adaptados_dict = {a['ejercicio_id']: a for a in adaptaciones}
    alertas_estancados = request.session.get('alertas_estancados', [])
    adaptaciones_positivas = request.session.pop('adaptaciones_positivas', [])
    adaptaciones_negativas = request.session.pop('adaptaciones_negativas', [])
    print("CONTENIDO DE ALERTAS ESTANCADOS:", alertas_estancados)
    print("ALERTAS ESTANCADOS:", request.session.get('alertas_estancados', []))
    alertas_ids = [a['ejercicio_id'] for a in alertas_estancados]
    alertas_dict = {a['ejercicio_id']: a for a in alertas_estancados}

    entreno = get_object_or_404(
        EntrenoRealizado.objects.select_related('cliente', 'rutina')
        .prefetch_related('series__ejercicio'), id=entreno_id
    )

    series_por_ejercicio = {}
    for serie in entreno.series.all():
        if serie.ejercicio.nombre not in series_por_ejercicio:
            series_por_ejercicio[serie.ejercicio.nombre] = []
        series_por_ejercicio[serie.ejercicio.nombre].append(serie)
    # IDs de todos los ejercicios que aparecen en este entreno
    ejercicio_ids_en_entreno = set(s.ejercicio.id for s in entreno.series.all())
    adaptados_ids = set(adaptados_ids)
    no_adaptados_ids = set(no_adaptados_ids)

    # Ejercicios que no están en adaptaciones ni no adaptaciones
    ejercicios_nuevos_ids = list(ejercicio_ids_en_entreno - adaptados_ids - no_adaptados_ids)
    # Contadores para el resumen
    resumen = {
        'total': 0,
        'adaptados': 0,
        'no_adaptados': 0,
        'nuevos': 0
    }

    # Todos los ejercicios realizados
    ejercicio_ids_en_entreno = set(s.ejercicio.id for s in entreno.series.all())
    resumen['total'] = len(ejercicio_ids_en_entreno)

    resumen['adaptados'] = len(adaptados_ids)
    resumen['no_adaptados'] = len(no_adaptados_ids)
    resumen['nuevos'] = len(ejercicio_ids_en_entreno - set(adaptados_ids) - set(no_adaptados_ids))
    acciones_estancamiento = request.session.pop('acciones_estancamiento', [])

    graficos_por_ejercicio = {}

    for nombre, series in series_por_ejercicio.items():
        ejercicio = series[0].ejercicio
        historial = SerieRealizada.objects.filter(
            ejercicio=ejercicio,
            entreno__cliente=entreno.cliente
        ).order_by('entreno__fecha')

        datos_por_fecha = defaultdict(list)
        for s in historial:
            datos_por_fecha[s.entreno.fecha].append(float(s.peso_kg))

        fechas = []
        promedios = []
        for fecha, pesos in datos_por_fecha.items():
            fechas.append(fecha.isoformat())
            promedios.append(round(sum(pesos) / len(pesos), 1))

        graficos_por_ejercicio[ejercicio.id] = {
            'labels': fechas,
            'data': promedios
        }

    context = {
        'entreno': entreno,
        'series_por_ejercicio': series_por_ejercicio,
        'adaptados_ids': adaptados_ids,
        'adaptados_dict': adaptados_dict,
        'no_adaptados_ids': no_adaptados_ids,
        'ejercicios_nuevos_ids': list(ejercicio_ids_en_entreno - set(adaptados_ids) - set(no_adaptados_ids)),
        'resumen': resumen,
        'alertas_ids': alertas_ids,
        'alertas_dict': alertas_dict,
        'acciones_estancamiento': request.session.pop('acciones_estancamiento', [])
    }

    context['graficos_por_ejercicio'] = json.dumps(graficos_por_ejercicio, cls=DjangoJSONEncoder)

    return render(request, 'entrenos/resumen_entreno.html', {
        'entreno': entreno,
        'series_por_ejercicio': series_por_ejercicio,
        'adaptados_ids': adaptados_ids,
        'adaptados_dict': adaptados_dict,
        'no_adaptados_ids': no_adaptados_ids,
        'ejercicios_nuevos_ids': list(ejercicio_ids_en_entreno - set(adaptados_ids) - set(no_adaptados_ids)),
        'resumen': resumen,
        'alertas_ids': alertas_ids,
        'alertas_dict': alertas_dict,
        'acciones_estancamiento': acciones_estancamiento,
        'adaptaciones_positivas': adaptaciones_positivas,
        'adaptaciones_negativas': adaptaciones_negativas,
    })
