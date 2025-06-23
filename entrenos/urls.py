# Archivo: entrenos/urls.py - URLs ACTUALIZADAS CON LIFTIN COMPLETO
from . import views_liftin
from django.urls import path
from . import views
from . import views
from .views_liftin import (
    importar_liftin_completo,
    importar_liftin_basico,
    buscar_entrenamientos_liftin,
    # ... otras vistas
)

app_name = 'entrenos'

urlpatterns = [
    # URLs originales (mantener compatibilidad)
    path('', views.entrenos_filtrados, name='entrenos_filtrados'),
    path('resumen/<str:rango>/', views.entrenos_filtrados, name='entrenos_filtrados'),
    path('historial/', views.historial_entrenos, name='historial_entrenos'),
    path('eliminar/<int:pk>/', views.eliminar_entreno, name='eliminar_entreno'),
    path('resumen/<int:entreno_id>/', views.resumen_entreno, name='resumen_entreno'),
    # path('entreno-anterior/<int:cliente_id>/<int:rutina_id>/', views.entreno_anterior, name='entreno_anterior'),

    # URLs de Liftin - Dashboard y funcionalidad básica
    path('liftin/', views.dashboard_liftin, name='dashboard_liftin'),
    path('liftin/importar/', views.importar_liftin, name='importar_liftin'),
    path('liftin/estadisticas/', views.estadisticas_liftin, name='estadisticas_liftin'),

    # URLs NUEVAS para Liftin Completo
    path('liftin/importar-completo/', views_liftin.importar_liftin_completo, name='importar_liftin_completo'),

    path('liftin/importar-basico/', views.importar_liftin_basico, name='importar_liftin_basico'),
    path('liftin/buscar/', views.buscar_entrenamientos_liftin, name='buscar_entrenamientos_liftin'),
    path('liftin/ejercicios/<int:entrenamiento_id>/', views.detalle_ejercicios_liftin,
         name='detalle_ejercicios_liftin'),
    path('entrenos/lista/', views.lista_entrenamientos, name='lista_entrenamientos'),

    # URLs de gestión y listado
    path('lista/', views.lista_entrenamientos, name='lista_entrenamientos'),
    path('detalle/<int:entrenamiento_id>/', views.detalle_entrenamiento, name='detalle_entrenamiento'),

    # URLs de exportación y análisis
    path('exportar/', views.exportar_datos, name='exportar_datos'),
    path('liftin/exportar/', views.exportar_datos_liftin, name='exportar_datos_liftin'),
    path('liftin/comparar/', views.comparar_liftin_manual, name='comparar_liftin_manual'),

    # APIs para datos dinámicos
    path('api/stats/', views.api_stats_dashboard, name='api_stats_dashboard'),
    path('api/liftin/stats/', views.api_stats_liftin, name='api_stats_liftin'),
    path('api/liftin/ejercicios/<int:entrenamiento_id>/', views.api_ejercicios_liftin, name='api_ejercicios_liftin'),

    # URLs de utilidades
    path('liftin/validar-datos/', views.validar_datos_liftin, name='validar_datos_liftin'),
    path('liftin/preview/', views.preview_importacion, name='preview_importacion'),
]
