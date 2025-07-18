from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone

from clientes.models import Cliente
from entrenos.models import EntrenoRealizado
from .models import (
    PerfilGamificacion, Logro, Quest, LogroUsuario,
    QuestUsuario, HistorialPuntos, Nivel, TipoLogro, TipoQuest
)
from .services import GamificacionService
from .models import (
    Notificacion,
    LogroUsuario,
    QuestUsuario,
    PerfilGamificacion,
    Logro,
    Quest,
    TipoLogro,
    TipoQuest
)
from .analysis import AnalisisGamificacionService

# logros/views.py - Añadir nuevas vistas
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_principal(request):
    """
    Vista principal del dashboard de gamificación
    """
    context = {
        'logros_completados': 12,  # Reemplaza con datos reales de tu modelo
        'total_logros': 25,
        'puntos_totales': 1250,
        'porcentaje_completado': 48,
        'nivel_actual': 3,
        'proxima_mision': 'Completar 5 entrenamientos esta semana',
        'notificaciones_pendientes': 3,
    }

    return render(request, 'logros/base_template.html', context)


@login_required
def analisis_cliente(request, cliente_id=None):
    """
    Muestra el análisis de datos de gamificación para un cliente específico.
    """
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        # Si no se especifica cliente, mostrar el primero (o redirigir a selección)
        cliente = Cliente.objects.first()
        if not cliente:
            messages.warning(request, "No hay clientes registrados.")
            return redirect('clientes:lista_clientes')

    # Obtener período de análisis (por defecto 90 días)
    periodo_dias = int(request.GET.get('periodo', 90))

    # Realizar análisis
    analisis = AnalisisGamificacionService.analisis_progreso_cliente(cliente, periodo_dias)

    context = {
        'cliente': cliente,
        'analisis': analisis,
        'periodo_dias': periodo_dias,
        'periodos_disponibles': [30, 90, 180, 365]
    }

    return render(request, 'logros/analisis_cliente.html', context)


@login_required
def analisis_global(request):
    """
    Muestra el análisis global de datos de gamificación para todos los clientes.
    """
    # Obtener período de análisis (por defecto 90 días)
    periodo_dias = int(request.GET.get('periodo', 90))

    # Realizar análisis global
    analisis = AnalisisGamificacionService.analisis_global_clientes(periodo_dias)

    context = {
        'analisis': analisis,
        'periodo_dias': periodo_dias,
        'periodos_disponibles': [30, 90, 180, 365]
    }

    return render(request, 'logros/analisis_global.html', context)


@login_required
def exportar_analisis_cliente_pdf(request, cliente_id):
    """
    Exporta el análisis de un cliente a PDF.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtener período de análisis (por defecto 90 días)
    periodo_dias = int(request.GET.get('periodo', 90))

    # Realizar análisis
    analisis = AnalisisGamificacionService.analisis_progreso_cliente(cliente, periodo_dias)

    # Generar PDF
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    import base64

    # Crear respuesta HTTP con PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analisis_{cliente.nombre}.pdf"'

    # Crear documento PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Contenido del PDF
    elements = []

    # Título
    elements.append(Paragraph(f"Análisis de Gamificación: {cliente.nombre}", styles['Title']))
    elements.append(Spacer(1, 12))

    # Período
    elements.append(Paragraph(f"Período de análisis: {periodo_dias} días", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Estadísticas generales
    elements.append(Paragraph("Estadísticas Generales", styles['Heading2']))
    elements.append(Paragraph(f"Entrenamientos totales: {analisis.get('entrenos_totales', 0)}", styles['Normal']))
    elements.append(Paragraph(f"Logros desbloqueados: {analisis.get('analisis_logros', {}).get('logros_totales', 0)}",
                              styles['Normal']))
    elements.append(Paragraph(f"Misiones completadas: {analisis.get('analisis_logros', {}).get('misiones_totales', 0)}",
                              styles['Normal']))
    elements.append(Spacer(1, 12))

    # Añadir gráficos
    if 'graficos' in analisis:
        for nombre, grafico_base64 in analisis['graficos'].items():
            # Convertir base64 a imagen
            grafico_data = grafico_base64.split(',')[1]
            grafico_binario = base64.b64decode(grafico_data)

            # Añadir imagen al PDF
            img = Image(BytesIO(grafico_binario), width=450, height=225)
            elements.append(img)
            elements.append(Spacer(1, 12))

    # Recomendaciones
    if 'recomendaciones' in analisis:
        elements.append(Paragraph("Recomendaciones", styles['Heading2']))
        for rec in analisis['recomendaciones']:
            elements.append(Paragraph(f"{rec['icono']} {rec['mensaje']}", styles['Normal']))
            elements.append(Spacer(1, 6))

    # Construir PDF
    doc.build(elements)

    # Obtener valor del buffer y escribirlo en la respuesta
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


@login_required
def perfil_gamificacion(request, cliente_id=None):
    """
    Muestra el perfil de gamificación de un cliente con sus logros, misiones y estadísticas.
    """
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        # Si no se especifica cliente, mostrar el primero (o redirigir a selección)
        cliente = Cliente.objects.first()
        if not cliente:
            messages.warning(request, "No hay clientes registrados.")
            return redirect('clientes:lista_clientes')

    # Obtener o crear perfil de gamificación
    perfil, created = PerfilGamificacion.objects.get_or_create(
        cliente=cliente,
        defaults={
            'nivel_actual': Nivel.objects.filter(numero=1).first()
        }
    )

    # Obtener logros desbloqueados
    logros_desbloqueados = LogroUsuario.objects.filter(
        perfil=perfil,
        completado=True
    ).select_related('logro', 'logro__tipo').order_by('-fecha_desbloqueo')

    # Obtener logros en progreso
    logros_progreso = LogroUsuario.objects.filter(
        perfil=perfil,
        completado=False
    ).select_related('logro', 'logro__tipo')

    # Filtrar logros secretos no desbloqueados
    logros_progreso = [lp for lp in logros_progreso if not lp.logro.es_secreto]

    # Obtener misiones activas
    misiones_activas = QuestUsuario.objects.filter(
        perfil=perfil,
        completada=False
    ).select_related('quest', 'quest__tipo')

    # Obtener misiones completadas recientemente
    misiones_completadas = QuestUsuario.objects.filter(
        perfil=perfil,
        completada=True
    ).select_related('quest', 'quest__tipo').order_by('-fecha_fin')[:10]

    # Obtener historial de puntos reciente
    historial_puntos = HistorialPuntos.objects.filter(
        perfil=perfil
    ).order_by('-fecha')[:20]

    # Calcular progreso hacia el siguiente nivel
    siguiente_nivel = None
    porcentaje_nivel = 100
    puntos_faltantes = 0

    if perfil.nivel_actual:
        siguiente_nivel = Nivel.objects.filter(
            puntos_requeridos__gt=perfil.nivel_actual.puntos_requeridos
        ).order_by('puntos_requeridos').first()

        if siguiente_nivel:
            puntos_nivel_actual = perfil.nivel_actual.puntos_requeridos
            puntos_siguiente_nivel = siguiente_nivel.puntos_requeridos
            rango_nivel = puntos_siguiente_nivel - puntos_nivel_actual

            if rango_nivel > 0:
                progreso_nivel = perfil.puntos_totales - puntos_nivel_actual
                porcentaje_nivel = min(100, int((progreso_nivel / rango_nivel) * 100))
                puntos_faltantes = puntos_siguiente_nivel - perfil.puntos_totales

    # Estadísticas adicionales
    estadisticas = {
        'total_logros': logros_desbloqueados.count(),
        'total_misiones': QuestUsuario.objects.filter(perfil=perfil, completada=True).count(),
        'entrenos_ultimo_mes': EntrenoRealizado.objects.filter(
            cliente=cliente,
            fecha__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
        'peso_total_levantado': EntrenoRealizado.objects.filter(
            cliente=cliente
        ).aggregate(
            total=Sum('series__peso_kg')
        )['total'] or 0
    }

    # Agrupar logros por categoría
    categorias_logros = {}
    for tipo in TipoLogro.objects.all():
        logros_categoria = [lu for lu in logros_desbloqueados if lu.logro.tipo_id == tipo.id]
        if logros_categoria:
            categorias_logros[tipo.get_categoria_display()] = logros_categoria

    # Agrupar misiones por período
    categorias_misiones = {}
    for tipo in TipoQuest.objects.all():
        misiones_categoria = [qu for qu in misiones_activas if qu.quest.tipo_id == tipo.id]
        if misiones_categoria:
            categorias_misiones[tipo.get_periodo_display()] = misiones_categoria

    context = {
        'cliente': cliente,
        'perfil': perfil,
        'logros_desbloqueados': logros_desbloqueados,
        'logros_progreso': logros_progreso,
        'misiones_activas': misiones_activas,
        'misiones_completadas': misiones_completadas,
        'historial_puntos': historial_puntos,
        'siguiente_nivel': siguiente_nivel,
        'porcentaje_nivel': porcentaje_nivel,
        'puntos_faltantes': puntos_faltantes,
        'estadisticas': estadisticas,
        'categorias_logros': categorias_logros,
        'categorias_misiones': categorias_misiones,
    }

    return render(request, 'logros/perfil_gamificacion.html', context)


@login_required
def lista_logros(request):
    """
    Muestra todos los logros disponibles en el sistema.
    """
    # Obtener todos los logros no secretos
    logros = Logro.objects.filter(es_secreto=False).select_related('tipo')

    # Agrupar por categoría
    categorias = {}
    for tipo in TipoLogro.objects.all():
        logros_categoria = [l for l in logros if l.tipo_id == tipo.id]
        if logros_categoria:
            categorias[tipo.get_categoria_display()] = logros_categoria

    context = {
        'categorias': categorias,
    }

    return render(request, 'logros/lista_logros.html', context)


@login_required
def lista_misiones(request):
    """
    Muestra todas las misiones disponibles en el sistema.
    """
    # Obtener todas las misiones activas
    misiones = Quest.objects.filter(activa=True).select_related('tipo')

    # Agrupar por período
    categorias = {}
    for tipo in TipoQuest.objects.all():
        misiones_categoria = [m for m in misiones if m.tipo_id == tipo.id]
        if misiones_categoria:
            categorias[tipo.get_periodo_display()] = misiones_categoria

    context = {
        'categorias': categorias,
    }

    return render(request, 'logros/lista_misiones.html', context)


@login_required
def ranking_clientes(request):
    """
    Muestra un ranking de clientes por puntos, logros y misiones.
    """
    # Obtener todos los perfiles ordenados por puntos
    perfiles = PerfilGamificacion.objects.all().select_related(
        'cliente', 'nivel_actual'
    ).order_by('-puntos_totales')

    # Añadir conteo de logros y misiones
    for perfil in perfiles:
        perfil.total_logros = LogroUsuario.objects.filter(
            perfil=perfil, completado=True
        ).count()

        perfil.total_misiones = QuestUsuario.objects.filter(
            perfil=perfil, completada=True
        ).count()

    context = {
        'perfiles': perfiles,
    }

    return render(request, 'logros/ranking_clientes.html', context)


@login_required
def procesar_entreno(request, entreno_id):
    """
    Procesa un entrenamiento para calcular puntos y verificar logros.
    """
    entreno = get_object_or_404(EntrenoRealizado, id=entreno_id)

    # Verificar que el entrenamiento no haya sido procesado ya
    if hasattr(entreno, 'procesado_gamificacion') and entreno.procesado_gamificacion:
        messages.info(request, "Este entrenamiento ya ha sido procesado para gamificación.")
        return redirect('entrenos:detalle_entreno', entreno_id=entreno.id)

    # Procesar el entrenamiento
    resultado = GamificacionService.procesar_entreno(entreno)

    if resultado:
        # Marcar como procesado
        entreno.procesado_gamificacion = True
        entreno.save(update_fields=['procesado_gamificacion'])

        # Mostrar mensaje de éxito con resultados
        mensaje = f"Entrenamiento procesado: +{resultado['puntos']} puntos"

        if resultado['logros_desbloqueados']:
            mensaje += f", {len(resultado['logros_desbloqueados'])} logros desbloqueados"

        if resultado['misiones_completadas']:
            mensaje += f", {len(resultado['misiones_completadas'])} misiones completadas"

        if resultado['subio_nivel']:
            mensaje += f". ¡Has subido al nivel {resultado['nivel_actual'].numero}!"

        messages.success(request, mensaje)

        # Redirigir al perfil de gamificación
        return redirect('logros:perfil_gamificacion', cliente_id=entreno.cliente.id)
    else:
        messages.error(request, "Error al procesar el entrenamiento para gamificación.")
        return redirect('entrenos:detalle_entreno', entreno_id=entreno.id)


@login_required
def detalle_logro(request, logro_id):
    """
    Muestra el detalle de un logro específico.
    """
    logro = get_object_or_404(Logro, id=logro_id)

    # Obtener usuarios que han desbloqueado este logro
    usuarios_logro = LogroUsuario.objects.filter(
        logro=logro,
        completado=True
    ).select_related('perfil', 'perfil__cliente').order_by('-fecha_desbloqueo')

    context = {
        'logro': logro,
        'usuarios_logro': usuarios_logro,
    }

    return render(request, 'logros/detalle_logro.html', context)


@login_required
def detalle_mision(request, quest_id):
    """
    Muestra el detalle de una misión específica.
    """
    quest = get_object_or_404(Quest, id=quest_id)

    # Obtener usuarios que han completado esta misión
    usuarios_quest = QuestUsuario.objects.filter(
        quest=quest,
        completada=True
    ).select_related('perfil', 'perfil__cliente').order_by('-fecha_fin')

    context = {
        'quest': quest,
        'usuarios_quest': usuarios_quest,
    }

    return render(request, 'logros/detalle_mision.html', context)


@login_required
def actualizar_progreso_ajax(request, cliente_id):
    """
    Endpoint AJAX para actualizar el progreso de logros y misiones.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtener perfil de gamificación
    perfil, created = PerfilGamificacion.objects.get_or_create(
        cliente=cliente,
        defaults={
            'nivel_actual': Nivel.objects.filter(numero=1).first()
        }
    )

    # Verificar logros y misiones
    logros_desbloqueados = GamificacionService.verificar_logros(perfil)
    misiones_completadas = GamificacionService.verificar_misiones(perfil)

    # Preparar respuesta
    nuevos_logros = []
    for logro in logros_desbloqueados:
        nuevos_logros.append({
            'id': logro.id,
            'nombre': logro.nombre,
            'descripcion': logro.descripcion,
            'puntos': logro.puntos_recompensa,
        })

    nuevas_misiones = []
    for mision in misiones_completadas:
        nuevas_misiones.append({
            'id': mision.id,
            'nombre': mision.nombre,
            'descripcion': mision.descripcion,
            'puntos': mision.puntos_recompensa,
        })

    # Actualizar nivel
    subio_nivel = perfil.actualizar_nivel()
    nivel_actual = {
        'numero': perfil.nivel_actual.numero,
        'nombre': perfil.nivel_actual.nombre,
    } if perfil.nivel_actual else None

    return JsonResponse({
        'success': True,
        'nuevos_logros': nuevos_logros,
        'nuevas_misiones': nuevas_misiones,
        'subio_nivel': subio_nivel,
        'nivel_actual': nivel_actual,
        'puntos_totales': perfil.puntos_totales,
    })


# logros/views.py - Añadir nuevas vistas

@login_required
def listar_notificaciones(request, cliente_id=None):
    """
    Muestra todas las notificaciones de un cliente.
    """
    from .models import Notificacion  # Añade esta línea

    cliente = get_object_or_404(Cliente, id=cliente_id)
    notificaciones = Notificacion.objects.filter(cliente=cliente).order_by('-fecha')

    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    else:
        # Si no se especifica cliente, mostrar el primero (o redirigir a selección)
        cliente = Cliente.objects.first()
        if not cliente:
            messages.warning(request, "No hay clientes registrados.")
            return redirect('clientes:lista_clientes')

    # Obtener todas las notificaciones del cliente
    notificaciones = Notificacion.objects.filter(cliente=cliente).order_by('-fecha')

    context = {
        'cliente': cliente,
        'notificaciones': notificaciones,
    }

    return render(request, 'logros/notificaciones.html', context)


@login_required
def marcar_todas_notificaciones_leidas(request, cliente_id):
    """
    Marca todas las notificaciones de un cliente como leídas.
    """
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=cliente_id)

        # Marcar todas como leídas
        Notificacion.objects.filter(
            cliente=cliente,
            leida=False
        ).update(leida=True)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=405)  # Method Not Allowed


@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación como leída y redirecciona.
    """
    # Obtener la notificación
    notificacion = get_object_or_404(Notificacion, id=notificacion_id)

    # Verificar que el usuario tenga acceso a esta notificación
    # (aquí podrías añadir más validaciones según tu lógica de permisos)

    # Marcar como leída
    notificacion.leida = True
    notificacion.save()

    # Si es una solicitud AJAX/POST, devolver JSON
    if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    # Redireccionar a la URL de acción si existe, o a la lista de notificaciones
    if notificacion.url_accion:
        return redirect(notificacion.url_accion)
    else:
        return redirect('logros:listar_notificaciones', cliente_id=notificacion.cliente.id)


@login_required
def obtener_notificaciones_ajax(request, cliente_id):
    from .models import Notificacion
    """
    Endpoint AJAX para obtener notificaciones no leídas.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtener notificaciones no leídas
    notificaciones = Notificacion.objects.filter(
        cliente=cliente,
        leida=False
    ).order_by('-fecha')[:5]  # Limitar a las 5 más recientes

    # Preparar datos para JSON
    data = []
    for notif in notificaciones:
        data.append({
            'id': notif.id,
            'tipo': notif.tipo,
            'titulo': notif.titulo,
            'mensaje': notif.mensaje,
            'icono': notif.icono,
            'fecha': notif.fecha.strftime('%d/%m/%Y %H:%M'),
            'url_accion': notif.url_accion,
        })

    return JsonResponse({'notificaciones': data})
