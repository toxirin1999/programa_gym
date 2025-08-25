# logros/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

from clientes.models import Cliente
from .models import (
    PerfilGamificacion, Arquetipo, PruebaLegendaria, PruebaUsuario,
    Quest, QuestUsuario, HistorialPuntos, Notificacion
)
from .services import CodiceService, AnalisisGamificacionService


@login_required
def perfil_gamificacion(request, cliente_id=None):
    """Vista principal del Códice de las Leyendas"""

    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        # Si no se especifica cliente, mostrar el primero disponible o redirigir
        cliente = Cliente.objects.first()
        if not cliente:
            messages.error(request, "No hay clientes registrados.")
            return redirect('clientes:lista_clientes')

    # Obtener o crear el perfil de gamificación
    perfil, created = PerfilGamificacion.objects.get_or_create(
        cliente=cliente,
        defaults={'nivel_actual': Arquetipo.objects.order_by('nivel').first()}
    )

    if created:
        messages.info(request, f"Se ha creado el perfil de gamificación para {cliente.nombre}.")

    # Obtener todos los arquetipos para mostrar la progresión
    todos_arquetipos = Arquetipo.objects.all().order_by('nivel')
    nivel_actual = perfil.nivel_actual.nivel if perfil.nivel_actual else 1

    # Preparar datos del códice
    codice = []
    for arquetipo in todos_arquetipos:
        # Determinar si este capítulo está desbloqueado
        desbloqueado = arquetipo.nivel <= nivel_actual

        if desbloqueado:
            # Obtener las pruebas de este arquetipo
            pruebas = PruebaLegendaria.objects.filter(arquetipo=arquetipo)
            pruebas_usuario = PruebaUsuario.objects.filter(
                perfil=perfil,
                prueba__in=pruebas
            ).select_related('prueba')

            # Crear diccionario de progreso por prueba
            progreso_pruebas = {pu.prueba.id: pu for pu in pruebas_usuario}

            pruebas_data = []
            for prueba in pruebas:
                if not prueba.es_secreta or prueba.id in progreso_pruebas:
                    pu = progreso_pruebas.get(prueba.id)
                    if pu:
                        progreso_actual = pu.progreso_actual
                        completada = pu.completada
                    else:
                        progreso_actual = 0
                        completada = False

                    porcentaje = min((progreso_actual / prueba.meta_valor) * 100, 100) if prueba.meta_valor > 0 else 0

                    pruebas_data.append({
                        'prueba': prueba,
                        'progreso_actual': progreso_actual,
                        'completada': completada,
                        'porcentaje': porcentaje,
                        'es_secreta': prueba.es_secreta and not completada
                    })

            # Calcular si el capítulo está dominado
            total_pruebas = len(pruebas_data)
            pruebas_completadas = sum(1 for p in pruebas_data if p['completada'])
            dominado = total_pruebas > 0 and pruebas_completadas == total_pruebas

            codice.append({
                'arquetipo': arquetipo,
                'desbloqueado': True,
                'dominado': dominado,
                'pruebas': pruebas_data,
                'progreso_capitulo': (pruebas_completadas / total_pruebas * 100) if total_pruebas > 0 else 0
            })
        else:
            # Capítulo bloqueado
            codice.append({
                'arquetipo': arquetipo,
                'desbloqueado': False,
                'dominado': False,
                'pruebas': [],
                'progreso_capitulo': 0
            })

    # Calcular progreso hacia el siguiente nivel
    siguiente_arquetipo = Arquetipo.objects.filter(nivel__gt=nivel_actual).order_by('nivel').first()
    progreso_siguiente_nivel = 0
    puntos_necesarios = 0

    if siguiente_arquetipo:
        puntos_actuales = perfil.puntos_totales
        puntos_nivel_actual = perfil.nivel_actual.puntos_requeridos if perfil.nivel_actual else 0
        puntos_siguiente_nivel = siguiente_arquetipo.puntos_requeridos

        if puntos_siguiente_nivel > puntos_nivel_actual:
            progreso_siguiente_nivel = ((puntos_actuales - puntos_nivel_actual) /
                                        (puntos_siguiente_nivel - puntos_nivel_actual)) * 100
            progreso_siguiente_nivel = min(max(progreso_siguiente_nivel, 0), 100)
            puntos_necesarios = max(puntos_siguiente_nivel - puntos_actuales, 0)

    # Obtener historial reciente de puntos
    historial_reciente = HistorialPuntos.objects.filter(
        perfil=perfil
    ).order_by('-fecha')[:10]

    # Obtener notificaciones no leídas
    notificaciones_no_leidas = Notificacion.objects.filter(
        perfil=perfil,
        leida=False
    ).order_by('-fecha_creacion')[:5]

    # Obtener quests activas (mantenemos la funcionalidad original)
    quests_activas = QuestUsuario.objects.filter(
        perfil=perfil,
        completada=False,
        quest__activa=True
    ).select_related('quest')[:5]

    context = {
        'cliente': cliente,
        'perfil': perfil,
        'codice': codice,
        'siguiente_arquetipo': siguiente_arquetipo,
        'progreso_siguiente_nivel': progreso_siguiente_nivel,
        'puntos_necesarios': puntos_necesarios,
        'historial_reciente': historial_reciente,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'quests_activas': quests_activas,
        'todos_los_clientes': Cliente.objects.all(),
    }

    return render(request, 'logros/perfil_gamificacion.html', context)


@login_required
def detalle_arquetipo(request, cliente_id, arquetipo_nivel):
    """Vista detallada de un arquetipo específico"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    arquetipo = get_object_or_404(Arquetipo, nivel=arquetipo_nivel)

    try:
        perfil = PerfilGamificacion.objects.get(cliente=cliente)
    except PerfilGamificacion.DoesNotExist:
        messages.error(request, "El cliente no tiene un perfil de gamificación.")
        return redirect('logros:perfil_gamificacion', cliente_id=cliente_id)

    # Verificar si el arquetipo está desbloqueado
    nivel_actual = perfil.nivel_actual.nivel if perfil.nivel_actual else 1
    if arquetipo.nivel > nivel_actual:
        messages.error(request, "Este capítulo aún no está desbloqueado.")
        return redirect('logros:perfil_gamificacion', cliente_id=cliente_id)

    # Obtener todas las pruebas del arquetipo
    pruebas = PruebaLegendaria.objects.filter(arquetipo=arquetipo)
    pruebas_usuario = PruebaUsuario.objects.filter(
        perfil=perfil,
        prueba__in=pruebas
    ).select_related('prueba')

    # Preparar datos de las pruebas
    progreso_pruebas = {pu.prueba.id: pu for pu in pruebas_usuario}
    pruebas_data = []

    for prueba in pruebas:
        pu = progreso_pruebas.get(prueba.id)
        if pu:
            progreso_actual = pu.progreso_actual
            completada = pu.completada
            fecha_completada = pu.fecha_completada
        else:
            progreso_actual = 0
            completada = False
            fecha_completada = None

        porcentaje = min((progreso_actual / prueba.meta_valor) * 100, 100) if prueba.meta_valor > 0 else 0

        pruebas_data.append({
            'prueba': prueba,
            'progreso_actual': progreso_actual,
            'completada': completada,
            'fecha_completada': fecha_completada,
            'porcentaje': porcentaje,
        })

    context = {
        'cliente': cliente,
        'perfil': perfil,
        'arquetipo': arquetipo,
        'pruebas_data': pruebas_data,
    }

    return render(request, 'logros/detalle_arquetipo.html', context)


@login_required
def lista_arquetipos(request):
    """Lista todos los arquetipos disponibles"""
    arquetipos = Arquetipo.objects.all().order_by('nivel')

    context = {
        'arquetipos': arquetipos,
    }

    return render(request, 'logros/lista_arquetipos.html', context)


@login_required
def lista_pruebas_legendarias(request):
    """Lista todas las pruebas legendarias disponibles"""
    pruebas = PruebaLegendaria.objects.all().select_related('arquetipo').order_by('arquetipo__nivel', 'nombre')

    # Filtros
    arquetipo_id = request.GET.get('arquetipo')
    if arquetipo_id:
        pruebas = pruebas.filter(arquetipo__nivel=arquetipo_id)

    mostrar_secretas = request.GET.get('secretas') == 'true'
    if not mostrar_secretas:
        pruebas = pruebas.filter(es_secreta=False)

    # Paginación
    paginator = Paginator(pruebas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'arquetipos': Arquetipo.objects.all().order_by('nivel'),
        'arquetipo_seleccionado': arquetipo_id,
        'mostrar_secretas': mostrar_secretas,
    }

    return render(request, 'logros/lista_pruebas_legendarias.html', context)


@login_required
def ranking_clientes(request):
    """Ranking de clientes por puntos totales"""
    perfiles = PerfilGamificacion.objects.select_related(
        'cliente', 'nivel_actual'
    ).order_by('-puntos_totales')

    # Añadir posición en el ranking
    for i, perfil in enumerate(perfiles, 1):
        perfil.posicion = i

    context = {
        'perfiles': perfiles,
    }

    return render(request, 'logros/ranking_clientes.html', context)


@login_required
def procesar_entreno(request, entreno_id):
    """Procesa manualmente la gamificación de un entrenamiento"""
    from entrenos.models import EntrenoRealizado

    entreno = get_object_or_404(EntrenoRealizado, id=entreno_id)

    try:
        resultado = CodiceService.procesar_entreno_completo(entreno)

        mensaje = f"Entrenamiento procesado exitosamente. "
        if resultado['pruebas_completadas']:
            mensaje += f"Pruebas completadas: {len(resultado['pruebas_completadas'])}. "
        if resultado['nivel_subido']:
            mensaje += "¡Nivel subido! "
        mensaje += f"Puntos totales: {resultado['puntos_totales']}"

        messages.success(request, mensaje)

    except Exception as e:
        messages.error(request, f"Error al procesar el entrenamiento: {str(e)}")

    return redirect('logros:perfil_gamificacion', cliente_id=entreno.cliente.id)


# --------------------------------------------------------------------------
# VISTAS DE ANÁLISIS (MANTIENEN LA FUNCIONALIDAD ORIGINAL)
# --------------------------------------------------------------------------

@login_required
def analisis_cliente(request, cliente_id):
    """Análisis de gamificación para un cliente específico"""
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtener período de análisis
    dias = int(request.GET.get('dias', 30))

    # Generar análisis
    analisis = AnalisisGamificacionService.analizar_cliente(cliente, dias)

    context = {
        'cliente': cliente,
        'analisis': analisis,
        'dias': dias,
    }

    return render(request, 'logros/analisis_cliente.html', context)


@login_required
def analisis_global(request):
    """Análisis global de gamificación"""
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)

    # Estadísticas generales
    total_perfiles = PerfilGamificacion.objects.count()
    total_puntos = PerfilGamificacion.objects.aggregate(
        total=Sum('puntos_totales')
    )['total'] or 0

    # Pruebas completadas en el período
    pruebas_completadas = PruebaUsuario.objects.filter(
        completada=True,
        fecha_completada__gte=fecha_inicio
    ).count()

    # Top 10 clientes
    top_clientes = PerfilGamificacion.objects.select_related(
        'cliente', 'nivel_actual'
    ).order_by('-puntos_totales')[:10]

    context = {
        'dias': dias,
        'total_perfiles': total_perfiles,
        'total_puntos': total_puntos,
        'pruebas_completadas': pruebas_completadas,
        'top_clientes': top_clientes,
    }

    return render(request, 'logros/analisis_global.html', context)


# --------------------------------------------------------------------------
# VISTAS DE NOTIFICACIONES
# --------------------------------------------------------------------------

@login_required
def listar_notificaciones(request, cliente_id):
    """Lista las notificaciones de un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)

    try:
        perfil = PerfilGamificacion.objects.get(cliente=cliente)
    except PerfilGamificacion.DoesNotExist:
        messages.error(request, "El cliente no tiene un perfil de gamificación.")
        return redirect('logros:perfil_gamificacion', cliente_id=cliente_id)

    notificaciones = Notificacion.objects.filter(
        perfil=perfil
    ).order_by('-fecha_creacion')

    # Paginación
    paginator = Paginator(notificaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'cliente': cliente,
        'perfil': perfil,
        'page_obj': page_obj,
    }

    return render(request, 'logros/notificaciones.html', context)


@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    if request.method == 'POST':
        notificacion = get_object_or_404(Notificacion, id=notificacion_id)
        notificacion.leida = True
        notificacion.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})


@login_required
def obtener_notificaciones_ajax(request, cliente_id):
    """Obtiene las notificaciones no leídas de un cliente vía AJAX"""
    cliente = get_object_or_404(Cliente, id=cliente_id)

    try:
        perfil = PerfilGamificacion.objects.get(cliente=cliente)
    except PerfilGamificacion.DoesNotExist:
        return JsonResponse({'notificaciones': []})

    notificaciones = Notificacion.objects.filter(
        perfil=perfil,
        leida=False
    ).order_by('-fecha_creacion')[:10]

    data = []
    for notif in notificaciones:
        data.append({
            'id': notif.id,
            'tipo': notif.tipo,
            'titulo': notif.titulo,
            'mensaje': notif.mensaje,
            'fecha': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        })

    return JsonResponse({'notificaciones': data})


# --------------------------------------------------------------------------
# VISTAS DE QUESTS (MANTIENEN LA FUNCIONALIDAD ORIGINAL)
# --------------------------------------------------------------------------

@login_required
def lista_misiones(request):
    """Lista todas las misiones disponibles"""
    misiones = Quest.objects.filter(activa=True).order_by('periodo', 'nombre')

    context = {
        'misiones': misiones,
    }

    return render(request, 'logros/lista_misiones.html', context)


@login_required
def detalle_mision(request, mision_id):
    """Detalle de una misión específica"""
    mision = get_object_or_404(Quest, id=mision_id)

    context = {
        'mision': mision,
    }

    return render(request, 'logros/detalle_mision.html', context)


# --------------------------------------------------------------------------
# EXPORTACIÓN A PDF
# --------------------------------------------------------------------------

@login_required
def exportar_analisis_cliente_pdf(request, cliente_id):
    """Exporta el análisis de un cliente a PDF"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    dias = int(request.GET.get('dias', 30))

    # Generar análisis
    analisis = AnalisisGamificacionService.analizar_cliente(cliente, dias)

    # Crear PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Análisis de Gamificación - {cliente.nombre}")

    # Contenido básico
    p.setFont("Helvetica", 12)
    y = 700

    if analisis['perfil']:
        p.drawString(100, y, f"Puntos totales: {analisis['perfil'].puntos_totales}")
        y -= 20
        p.drawString(100, y, f"Nivel actual: {analisis['nivel_actual']}")
        y -= 20
        p.drawString(100, y, f"Racha actual: {analisis['racha_actual']} días")
        y -= 20
        p.drawString(100, y, f"Puntos en los últimos {dias} días: {analisis['puntos_periodo']}")
    else:
        p.drawString(100, y, "El cliente no tiene datos de gamificación.")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analisis_{cliente.nombre}_{dias}dias.pdf"'

    return response
