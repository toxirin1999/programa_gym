from django.urls import path
from . import views

app_name = 'logros'

urlpatterns = [
    # Perfil de gamificación
    path('perfil/', views.perfil_gamificacion, name='perfil_gamificacion'),
    path('perfil/<int:cliente_id>/', views.perfil_gamificacion, name='perfil_gamificacion'),

    # Logros
    path('logros/', views.lista_logros, name='lista_logros'),
    path('logros/<int:logro_id>/', views.detalle_logro, name='detalle_logro'),

    # Misiones
    path('misiones/', views.lista_misiones, name='lista_misiones'),
    path('misiones/<int:quest_id>/', views.detalle_mision, name='detalle_mision'),

    # Ranking
    path('ranking/', views.ranking_clientes, name='ranking_clientes'),

    # Procesamiento de entrenamientos
    path('procesar-entreno/<int:entreno_id>/', views.procesar_entreno, name='procesar_entreno'),

    # AJAX
    path('actualizar-progreso/<int:cliente_id>/', views.actualizar_progreso_ajax, name='actualizar_progreso_ajax'),
    # Notificaciones
    path('notificaciones/<int:cliente_id>/', views.listar_notificaciones, name='listar_notificaciones'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida,
         name='marcar_notificacion_leida'),
    path('api/notificaciones/<int:cliente_id>/', views.obtener_notificaciones_ajax, name='obtener_notificaciones_ajax'),
    path('notificaciones/marcar-todas-leidas/<int:cliente_id>/', views.marcar_todas_notificaciones_leidas,
         name='marcar_todas_notificaciones_leidas'),
    path('analisis/cliente/<int:cliente_id>/', views.analisis_cliente, name='analisis_cliente'),
    path('analisis/global/', views.analisis_global, name='analisis_global'),
    path('analisis/cliente/<int:cliente_id>/exportar-pdf/', views.exportar_analisis_cliente_pdf,
         name='exportar_analisis_cliente_pdf'),
]
