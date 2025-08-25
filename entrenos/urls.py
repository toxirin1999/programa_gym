# ============================================================================
# URLs CORREGIDAS PARA LIFTIN - entrenos/urls.py
# ============================================================================

# REEMPLAZAR el contenido de entrenos/urls.py con este código:
from django.urls import path
from . import views
from . import views_liftin
from .views import ejercicios_realizados_view
from clientes import views as vistas_clientes

app_name = 'entrenos'

urlpatterns = [
    # ============================================================================
    # URLs ORIGINALES (mantener tal como están)
    # ============================================================================
    path('resumen/<int:pk>/', views.resumen_entreno, name='resumen_entreno'),
    # URL más general después
    path('resumen/<str:rango>/', views.entrenos_filtrados, name='entrenos_filtrados_rango'),
    # Renombrada para evitar conflicto
    path('plan-anual/<int:cliente_id>/', views.vista_plan_anual, name='vista_plan_anual'),
    path('historial-detallado/', views.historial_entrenos, name='historial_entrenos'),
    # path('eliminar/<int:pk>/', views.eliminar_entreno, name='eliminar_entreno'),
    path('ejercicio/<str:nombre>/', views.detalle_ejercicio, name='detalle_ejercicio'),
    path('tabla-ejercicios/', views.ejercicios_realizados_view, name='tabla_ejercicios'),
    path('gestionar-base/', views.gestionar_ejercicios_base, name='gestionar_ejercicios_base'),

    # --- VISTAS DEL PLANIFICADOR Y ENTRENAMIENTO ACTIVO ---
    path('cliente/<int:cliente_id>/entrenamiento-activo/', views.vista_entrenamiento_activo,
         name='entrenamiento_activo'),
    path('cliente/<int:cliente_id>/guardar-entrenamiento/', views.guardar_entrenamiento_activo,
         name='guardar_entrenamiento_activo'),

    # ============================================================================
    # URLs DE LIFTIN CORREGIDAS
    # ============================================================================

    # Dashboard principal de Liftin
    path('liftin/', views_liftin.dashboard_liftin, name='dashboard_liftin'),
    path('gestionar-base/', views.gestionar_ejercicios_base, name='gestionar_ejercicios_base'),
    path('tabla-ejercicios/', ejercicios_realizados_view, name='tabla_ejercicios'),

    # Dashboard por cliente específico
    path('liftin/cliente/<int:cliente_id>/', views_liftin.dashboard_liftin_cliente, name='dashboard_liftin_cliente'),

    # Importación
    path('liftin/importar/', views_liftin.importar_liftin, name='importar_liftin'),
    path('liftin/importar-completo/', views_liftin.importar_liftin_completo, name='importar_liftin_completo'),

    # Estadísticas de Liftin
    path('liftin/estadisticas/', views_liftin.estadisticas_liftin, name='estadisticas_liftin'),

    # ⭐ NUEVA: Exportación (corrige el error de URL)
    path('liftin/exportar/', views_liftin.exportar_datos_liftin, name='exportar_datos_liftin'),

    # Detalles y gestión
    path('liftin/ejercicios/<int:entreno_id>/', views_liftin.detalle_ejercicios_liftin,
         name='detalle_ejercicios_liftin'),
    # ⭐ NUEVAS: Edición y eliminación de entrenamientos
    path('liftin/editar/<int:entrenamiento_id>/', views_liftin.editar_entrenamiento_liftin,
         name='editar_entrenamiento_liftin'),
    path('liftin/eliminar/<int:entrenamiento_id>/', views_liftin.eliminar_entrenamiento_liftin,
         name='eliminar_entrenamiento_liftin'),

    # Búsqueda y filtros
    path('liftin/buscar/', views_liftin.buscar_entrenamientos_liftin, name='buscar_entrenamientos_liftin'),
    path('liftin/comparar/', views_liftin.comparar_liftin_manual, name='comparar_liftin_manual'),

    # ============================================================================
    # ============================================================================
    # APIs PARA DATOS DINÁMICOS
    # ============================================================================
    path('api/liftin/stats/', views_liftin.api_stats_liftin, name='api_stats_liftin'),
    path('api/liftin/ejercicios/<int:entrenamiento_id>/', views_liftin.api_ejercicios_liftin,
         name='api_ejercicios_liftin'),

    # ============================================================================
    # URLs DE GESTIÓN GENERAL
    # ============================================================================
    path('lista/', views.lista_entrenamientos, name='lista_entrenamientos'),
    path('detalle/<int:entrenamiento_id>/', views.detalle_entrenamiento, name='detalle_entrenamiento'),

    path('whoop/registro/', views.registrar_whoop, name='registrar_whoop'),
    path('whoop/tarjeta/', views.tarjeta_whoop, name='tarjeta_whoop'),
    # si haces una vista tipo resumen

    path('cliente/<int:cliente_id>/plan/', views.vista_plan_calendario, name='vista_plan_calendario'),
    path('cliente/<int:cliente_id>/preferencias-helms/', vistas_clientes.configurar_preferencias_helms,
         name='configurar_preferencias_helms'),
    path('cliente/<int:cliente_id>/dashboard-adherencia/', vistas_clientes.dashboard_adherencia,
         name='dashboard_adherencia'),
    # APIs para funcionalidad avanzada
    path('api/cliente/<int:cliente_id>/regenerar-plan/', views.api_regenerar_plan_helms, name='api_regenerar_plan'),
    path('cliente/<int:cliente_id>/comparacion/', views.dashboard_comparacion_planificadores,
         name='dashboard_comparacion'),
    path('resumen-anual/<int:cliente_id>/', views.vista_resumen_anual, name='vista_resumen_anual'),
    
]
