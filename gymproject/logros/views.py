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
