from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import LogroDesbloqueado, EstadoEmocional

from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _
from types import SimpleNamespace
import copy
from types import SimpleNamespace
from django.shortcuts import render, get_object_or_404
from .models import EntrenoRealizado, SerieRealizada
from django.db.models import Count, Avg, Sum
import json
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
from rutinas.models import Rutina, RutinaEjercicio, Ejercicio
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
    progreso_fechas = ['22 May', '23 May', '24 May', '25 May', '26 May', '27 May', '28 May']
    progreso_valores = [2600, 2800, 3000, 2900, 3100, 3300, 3500]

    # Añadir información de depuración al contexto
    context = {
        'cliente': cliente,
        'rutina': rutina,
        'ultimo_logro': ultimo_logro,
        'estado_emocional': estado_emocional,
        'progreso_fechas': progreso_fechas,
        'progreso_valores': progreso_valores,
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
from rutinas.models import Ejercicio, Rutina, RutinaEjercicio

logger = logging.getLogger(__name__)


# Clase para codificar Decimal y datetime en JSON (Mantén solo una vez)
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# --- FUNCIÓN resumen_entreno CORREGIDA Y OPTIMIZADA ---
def resumen_entreno(request, entreno_id):
    try:
        entreno_actual = get_object_or_404(EntrenoRealizado, id=entreno_id)
        cliente = entreno_actual.cliente
        rutina = entreno_actual.rutina
    except Exception as e:
        logger.error(f"Error al cargar entreno o cliente en resumen_entreno: {e}")
        messages.error(request, "No se encontró el entrenamiento o no tienes permisos.")
        return redirect('historial_entrenos')

    # --- 1. Datos para Detalles del Entrenamiento Actual ---
    series_entreno_actual = SerieRealizada.objects.filter(entreno=entreno_actual).order_by('ejercicio__nombre',
                                                                                           'serie_numero')
    entreno_actual_data = []
    for serie in series_entreno_actual:
        entreno_actual_data.append({
            'ejercicio_nombre': serie.ejercicio.nombre,
            'serie_numero': serie.serie_numero,
            'repeticiones': serie.repeticiones,
            'peso_kg': float(serie.peso_kg) if serie.peso_kg is not None else 0.0,
            'completado': serie.completado,
        })
    series_totales = series_entreno_actual.count()
    series_exitosas = series_entreno_actual.filter(completado=True).count()
    entreno_perfecto = series_totales > 0 and series_exitosas == series_totales
    entreno_actual_json = json.dumps(entreno_actual_data, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 2. Lógica para Logros de Hoy ---
    hoy = date.today()
    logros_hoy = {'mensaje': 'Aún no hay datos de logros para hoy.', 'total_peso_levantado_hoy': 0.0}
    try:
        total_peso_hoy = SerieRealizada.objects.filter(
            entreno__cliente=cliente,
            entreno__fecha=hoy
        ).aggregate(total=Sum('peso_kg'))['total'] or Decimal('0.0')

        logros_hoy['total_peso_levantado_hoy'] = float(total_peso_hoy.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        logros_hoy['mensaje'] = f"¡Hoy levantaste un total de {logros_hoy['total_peso_levantado_hoy']} kg!"
    except Exception as e:
        logger.error(f"Error al calcular logros de hoy: {e}")
        logros_hoy = {'mensaje': "Error al cargar los logros de hoy.", 'total_peso_levantado_hoy': 0.0, 'error': True}
    logros_hoy_json = json.dumps(logros_hoy, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 3. Lógica para Sugerencias Inteligentes ---
    sugerencias = []
    try:
        series_fallidas = [s for s in series_entreno_actual if not s.completado]
        if series_fallidas:
            sugerencias.append("Considera revisar la técnica o reducir ligeramente el peso en los ejercicios fallidos.")
        else:
            sugerencias.append("¡Excelente rendimiento! Sigue así.")
    except Exception as e:
        logger.error(f"Error al generar sugerencias: {e}")
        sugerencias = ["Error al cargar sugerencias."]
    sugerencias_inteligentes_json = json.dumps(sugerencias, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 4. Lógica para Predicciones de Progreso ---
    predicciones = {'mensaje': "No hay datos suficientes para predecir el progreso.", 'tendencia': 'insuficiente'}
    try:
        ultimos_entrenos_ejercicio = SerieRealizada.objects.filter(
            entreno__cliente=cliente,
        ).order_by('-entreno__fecha', '-entreno__id', '-serie_numero')[:5]

        pesos = [float(s.peso_kg) for s in ultimos_entrenos_ejercicio if s.peso_kg is not None]

        if len(pesos) >= 2:
            promedio_reciente = sum(pesos[:2]) / len(pesos[:2])
            promedio_anterior = sum(pesos[2:]) / len(pesos[2:]) if len(pesos[2:]) > 0 else 0
            if promedio_reciente > promedio_anterior:
                predicciones['mensaje'] = "¡Tendencia al alza en el peso levantado! Buen progreso."
                predicciones['tendencia'] = 'ascendente'
            elif promedio_reciente < promedio_anterior and promedio_anterior != 0:
                predicciones['mensaje'] = "El peso levantado ha disminuido ligeramente. Revisa tu descanso."
                predicciones['tendencia'] = 'descendente'
            else:
                predicciones['mensaje'] = "Progreso estable."
                predicciones['tendencia'] = 'estable'
        else:
            predicciones['mensaje'] = "Necesitas más datos de entrenamiento para predecir el progreso."
            predicciones['tendencia'] = 'insuficiente'
    except Exception as e:
        logger.error(f"Error al generar predicciones: {e}")
        predicciones = {'mensaje': "Error al cargar predicciones.", 'tendencia': 'error', 'error': True}
    predicciones_progreso_json = json.dumps(predicciones, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 5. Lógica para Medallas y Logros ---
    medallas_logros = []
    try:
        entrenos_cliente = EntrenoRealizado.objects.filter(cliente=cliente)
        entrenos_perfectos_count = 0  # Usar un nombre diferente para evitar confusión con entreno_perfecto del actual

        for entreno in entrenos_cliente:
            total_series_entreno = SerieRealizada.objects.filter(entreno=entreno).count()
            completadas_series_entreno = SerieRealizada.objects.filter(entreno=entreno, completado=True).count()
            if total_series_entreno > 0 and total_series_entreno == completadas_series_entreno:
                entrenos_perfectos_count += 1

        entrenos_completados_count = entrenos_cliente.count()

        if entrenos_completados_count >= 5:
            medallas_logros.append(
                {'nombre': 'Constancia', 'descripcion': 'Completaste 5+ entrenamientos.', 'tipo': 'medalla'})
        if entrenos_completados_count >= 10:
            # Eliminar la medalla de constancia básica si ya se tiene la avanzada
            if {'nombre': 'Constancia', 'descripcion': 'Completaste 5+ entrenamientos.',
                'tipo': 'medalla'} in medallas_logros:
                medallas_logros.remove(
                    {'nombre': 'Constancia', 'descripcion': 'Completaste 5+ entrenamientos.', 'tipo': 'medalla'})
            medallas_logros.append(
                {'nombre': 'Constancia Avanzada', 'descripcion': 'Completaste 10+ entrenamientos.', 'tipo': 'medalla'})

        # Actualizar contador de entrenos perfectos del cliente (si el entreno actual fue perfecto)
        if entreno_perfecto:
            if not hasattr(cliente, 'entrenos_perfectos_totales') or cliente.entrenos_perfectos_totales is None:
                cliente.entrenos_perfectos_totales = 0  # Inicializar si no existe o es None
            cliente.entrenos_perfectos_totales += 1
            cliente.save()  # Guarda el contador actualizado

        # Medalla de Precisión (basada en el contador total)
        if hasattr(cliente, 'entrenos_perfectos_totales') and cliente.entrenos_perfectos_totales >= 1:
            medallas_logros.append({
                'nombre': 'Precisión',
                'descripcion': f'{cliente.entrenos_perfectos_totales} entrenos perfectos (100% completado)',
                'tipo': 'medalla'
            })
    except Exception as e:
        logger.error(f"Error al generar medallas y logros: {e}")
        medallas_logros = [{'nombre': 'Error', 'descripcion': 'No se pudieron cargar las medallas.', 'tipo': 'error'}]
    medallas_logros_json = json.dumps(medallas_logros, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 6. Lógica para Tablas de Clasificación (Leaderboard) ---
    leaderboard_data = []  # Inicialización segura
    try:
        top_clientes_entrenos = Cliente.objects.annotate(
            num_entrenos=Count('entrenorealizado')
        ).order_by('-num_entrenos')[:5]
        for c in top_clientes_entrenos:
            leaderboard_data.append({'nombre': c.nombre, 'valor': c.num_entrenos, 'unidad': 'entrenos'})
    except Exception as e:
        logger.error(f"Error al generar leaderboard: {e}")
        leaderboard_data = [{'nombre': 'Error', 'valor': 0, 'unidad': 'datos no disponibles'}]
    leaderboard_json = json.dumps(leaderboard_data, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- 7. Lógica para Progreso por Ejercicio ---
    progreso_por_ejercicio = {}  # Inicialización segura
    try:
        # Obtener todos los ejercicios del entreno actual (para filtrar los históricos relevantes)
        ejercicios_en_entreno_actual = set(serie.ejercicio for serie in series_entreno_actual)

        for ejercicio in ejercicios_en_entreno_actual:
            series_historicas = SerieRealizada.objects.filter(
                entreno__cliente=cliente,
                ejercicio=ejercicio
            ).order_by('entreno__fecha').values('entreno__fecha').annotate(
                peso_promedio=Avg('peso_kg'),
                reps_promedio=Avg('repeticiones')
            )
            # Asegúrate de que los valores sean floats y enteros, y que las listas no estén vacías
            if series_historicas:
                progreso_por_ejercicio[ejercicio.nombre] = {
                    "labels": [DateFormat(d["entreno__fecha"]).format("d M") for d in series_historicas],
                    "peso": [round(float(d["peso_promedio"] or 0), 1) for d in series_historicas],
                    "reps": [int(d["reps_promedio"] or 0) for d in series_historicas]
                }
            else:
                # Si no hay datos históricos para este ejercicio, inicializa con listas vacías
                progreso_por_ejercicio[ejercicio.nombre] = {
                    "labels": [], "peso": [], "reps": []
                }
    except Exception as e:
        logger.error(f"Error al generar progreso por ejercicio: {e}")
        progreso_por_ejercicio = {"error": "No se pudo cargar el progreso de ejercicios.", 'error': True}
    progreso_por_ejercicio_json = json.dumps(progreso_por_ejercicio, cls=CustomJSONEncoder, ensure_ascii=False)

    # --- Pasa todos los JSON y otros datos al contexto del template ---
    progreso_semanal = {
        "peso_total_esta_semana": 19800,
        "peso_total_anterior": 17500,
        "rondas_completas": 3
    }
    logros = {
        "ejercicios_mejorados": 2  # valor real desde tu lógica
    }
    consistencia = {
        "entrenos_esta_semana": 4,
        "historial": [True, True, True, True, False, False, False],
        "semanas_consecutivas": 6
    }
    carga = {
        "diferencia": 2700  # positivo o negativo, según cálculo real
    }
    context = {
        'entreno_actual': entreno_actual,
        'entreno_actual_json': entreno_actual_json,
        'logros_hoy_json': logros_hoy_json,
        'sugerencias_inteligentes_json': sugerencias_inteligentes_json,
        'predicciones_progreso_json': predicciones_progreso_json,
        'medallas_logros_json': medallas_logros_json,
        'leaderboard_json': leaderboard_json,  # Aquí se usa la variable correcta
        'entreno_perfecto': entreno_perfecto,  # Este es un booleano, no JSON
        "progreso_por_ejercicio_json": progreso_por_ejercicio_json,
        "progreso_semanal_json": json.dumps(progreso_semanal, ensure_ascii=False),
        'logros': logros,
        "consistencia": consistencia,
        "carga": carga
    }
    return render(request, 'entrenos/resumen_entreno.html', context)
# --- FIN DE LA VISTA resumen_entreno ---

# (El resto de tus vistas y funciones como entrenos_filtrados, historial_entrenos,
# crear_entreno, adaptar_plan_personalizado, etc. continúan aquí)
# ...
