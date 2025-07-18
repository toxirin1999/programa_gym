# 🔗 URLs del sistema de Inteligencia Artificial Avanzada
# Archivo: analytics/urls.py

from django.urls import path
from . import views
from . import views_ia
from .views_planificacion import vista_plan_optimo
from .analisis_intensidad import dashboard_intensidad_avanzado
from analytics.analisis_progresion import dashboard_progresion_avanzado
from analytics.ia_deteccion_patrones2 import deteccion_patrones_view

app_name = 'analytics'

urlpatterns = [
    # ==================== DASHBOARDS PRINCIPALES ====================
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_default'),
    path('dashboard/<int:cliente_id>/', views.dashboard, name='dashboard_cliente'),

    path('ia/dashboard/<int:cliente_id>/', views_ia.dashboard_ia_principal, name='dashboard_ia_principal'),

    # ==================== MÓDULOS DETALLADOS (LEGACY) ====================
    path('progresion/<int:cliente_id>/', views.analisis_progresion, name='progresion'),
    path('comparativas/<int:cliente_id>/', views.comparativas, name='comparativas'),
    path('recomendaciones/<int:cliente_id>/', views.recomendaciones, name='recomendaciones'),
    path('predicciones/<int:cliente_id>/', views.predicciones, name='predicciones'),

    path('intensidad-avanzado/<int:cliente_id>/', dashboard_intensidad_avanzado, name='intensidad_avanzado'),
    path('progresion-avanzado/<int:cliente_id>/', dashboard_progresion_avanzado, name='progresion_avanzado'),

    path('cliente/<int:cliente_id>/plan-optimo/', vista_plan_optimo, name='vista_plan_optimo'),

    path('detectar_patrones/<int:cliente_id>/', deteccion_patrones_view, name='detectar_patrones'),

    # ==================== FUNCIONES (LEGACY) ====================
    path('calcular-metricas/<int:cliente_id>/', views.calcular_metricas, name='calcular_metricas'),
    path('generar-recomendaciones/<int:cliente_id>/', views.generar_recomendaciones, name='generar_recomendaciones'),
    path('recomendacion/<int:recomendacion_id>/aplicar/', views.marcar_recomendacion_aplicada,
         name='aplicar_recomendacion'),

    path('api/ejercicios/<int:cliente_id>/', views.api_ejercicios_tabla, name='api_ejercicios'),
    path('api/metricas/<int:cliente_id>/', views.api_metricas_tabla, name='api_metricas'),
    path('api/progresion/<int:cliente_id>/<str:ejercicio>/', views.api_progresion, name='api_progresion'),

    path('actualizar_tendencias/<int:cliente_id>/', views.actualizar_tendencias, name='actualizar_tendencias'),

    # ==================== MÓDULOS INTELIGENTES (IA) ====================
    path('ia/predicciones/<int:cliente_id>/', views_ia.predicciones_avanzadas, name='predicciones_avanzadas'),
    path('ia/recomendaciones/<int:cliente_id>/', views_ia.recomendaciones_inteligentes,
         name='recomendaciones_inteligentes'),
    path('ia/patrones/<int:cliente_id>/', views_ia.deteccion_patrones_automatica, name='deteccion_patrones'),
    path('ia/optimizacion/<int:cliente_id>/', views_ia.vista_optimizacion_entrenamientos,
         name='vista_optimizacion_entrenamientos'),

    # ==================== API EN TIEMPO REAL (AJAX/JS) ====================
    path('api/dashboard-refresh/<int:cliente_id>/', views_ia.api_dashboard_refresh, name='api_dashboard_refresh'),

    path('api/prediccion-tiempo-real/<int:cliente_id>/', views_ia.api_prediccion_tiempo_real,
         name='api_prediccion_tiempo_real'),
    path('api/recomendacion-tiempo-real/<int:cliente_id>/', views_ia.api_recomendacion_tiempo_real,
         name='api_recomendacion_tiempo_real'),
    path('api/deteccion-patrones-tiempo-real/<int:cliente_id>/', views_ia.api_deteccion_patrones_tiempo_real,
         name='api_deteccion_patrones_tiempo_real'),
    path('api/optimizacion-tiempo-real/<int:cliente_id>/', views_ia.api_optimizacion_tiempo_real,
         name='api_optimizacion_tiempo_real'),

    # ==================== RUTAS ALTERNATIVAS (COMPATIBILIDAD IMPORTS) ====================
    path('ia/patrones-view/<int:cliente_id>/', views_ia.deteccion_patrones_view, name='deteccion_patrones_view'),
]
