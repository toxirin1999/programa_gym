from django.urls import path
from . import views
from clientes import views as clientes_views
from .views import historial_cliente

# clientes/urls.py
from django.urls import path
from . import views
from clientes import views as clientes_views
from .views import historial_cliente  # Asumiendo que esta importación es necesaria para alguna otra URL
from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import redirigir_usuario
from .views import panel_cliente
from clientes import views
from joi import views as joi_views

urlpatterns = [
    # Clientes
    path('agregar/', views.agregar_cliente, name='agregar_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('detalle/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('programa/<int:programa_id>/asignar_cliente/', views.asignar_programa_a_cliente,
         name='asignar_programa_a_cliente'),
    path('cliente/<int:cliente_id>/revisiones/', views.lista_revisiones, name='lista_revisiones'),
    path('historial/exportar/<int:cliente_id>/', views.exportar_historial, name='exportar_historial'),
    path('cliente/<int:cliente_id>/revisiones/agregar/', views.agregar_revision, name='agregar_revision'),
    path('cliente/<int:cliente_id>/asignar_dieta/', views.asignar_dieta_directo, name='asignar_dieta_directo'),
    path('panel/', clientes_views.dashboard, name='dashboard'),

    # Esta es la URL correcta para el cálculo y visualización del plan nutricional
    path('nutricion/calcular/', views.calcular_plan_nutricional, name='calcular_plan_nutricional'),

    # ELIMINA LA SIGUIENTE LÍNEA, YA QUE LA FUNCIÓN 'plan_nutricional_resultado' NO EXISTE:
    # path('/nutricion/plan_resultado/', views.plan_nutricional_resultado, name='plan_nutricional_resultado'),
    path('', login_required(redirigir_usuario), name='home_redirect'),
    path('datos-graficas/<int:cliente_id>/', views.datos_graficas, name='datos_graficas'),
    # Medidas (con prefijo para no pisar rutas de clientes)
    path('medidas/', views.lista_medidas, name='lista_medidas'),
    path('historial/<int:cliente_id>/', historial_cliente, name='historial_cliente'),
    path('mi-panel/', panel_cliente, name='panel_cliente'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('registrar_emocion/', views.registrar_emocion, name='registrar_emocion'),
    path('inicio/', joi_views.inicio_view, name='joi_inicio'),

    path('cliente/<int:cliente_id>/recordatorio/', views.actualizar_recordatorio_peso,
         name='actualizar_recordatorio_peso'),
    path('cliente/<int:cliente_id>/objetivo/', views.definir_objetivo, name='definir_objetivo'),
    path('revision/<int:revision_id>/eliminar/', views.eliminar_revision, name='eliminar_revision'),

    path('objetivo/<int:pk>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('objetivo/<int:pk>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),
    path('comparar/', views.comparar_clientes, name='comparar_clientes'),
    path('comparar/datos/', views.datos_comparacion, name='datos_comparacion'),
    path('medidas/agregar/', views.agregar_medida, name='agregar_medida'),
]
