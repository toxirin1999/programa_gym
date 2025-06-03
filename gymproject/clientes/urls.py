from django.urls import path
from . import views
from clientes import views as clientes_views
from .views import historial_cliente, redirigir_usuario, panel_cliente
from django.contrib.auth.decorators import login_required
from joi import views as joi_views

urlpatterns = [
    # Vista raíz: lista de clientes (entrenador)
    path('', views.lista_clientes, name='lista_clientes'),

    # Clientes
    path('agregar/', views.agregar_cliente, name='agregar_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('detalle/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('programa/<int:programa_id>/asignar_cliente/', views.asignar_programa_a_cliente,
         name='asignar_programa_a_cliente'),
    path('cliente/<int:cliente_id>/revisiones/', views.lista_revisiones, name='lista_revisiones'),
    path('cliente/<int:cliente_id>/revisiones/agregar/', views.agregar_revision, name='agregar_revision'),
    path('historial/exportar/<int:cliente_id>/', views.exportar_historial, name='exportar_historial'),
    path('cliente/<int:cliente_id>/asignar_dieta/', views.asignar_dieta_directo, name='asignar_dieta_directo'),

    # Paneles
    path('panel/', clientes_views.dashboard, name='dashboard'),
    path('mi-panel/', panel_cliente, name='panel_cliente'),

    # Nutrición
    path('nutricion/calcular/', views.calcular_plan_nutricional, name='calcular_plan_nutricional'),

    # Redirección inteligente (manual, no raíz)
    path('inicio/', login_required(redirigir_usuario), name='redirigir_usuario'),

    # Datos y medidas
    path('datos-graficas/<int:cliente_id>/', views.datos_graficas, name='datos_graficas'),
    path('medidas/', views.lista_medidas, name='lista_medidas'),
    path('medidas/agregar/', views.agregar_medida, name='agregar_medida'),

    # Historial
    path('historial/<int:cliente_id>/', historial_cliente, name='historial_cliente'),

    # Joi
    path('inicio-joi/', joi_views.inicio_view, name='joi_inicio'),

    # Emoción y objetivos
    path('registrar_emocion/', views.registrar_emocion, name='registrar_emocion'),
    path('cliente/<int:cliente_id>/recordatorio/', views.actualizar_recordatorio_peso,
         name='actualizar_recordatorio_peso'),
    path('cliente/<int:cliente_id>/objetivo/', views.definir_objetivo, name='definir_objetivo'),
    path('revision/<int:revision_id>/eliminar/', views.eliminar_revision, name='eliminar_revision'),
    path('objetivo/<int:pk>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('objetivo/<int:pk>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),

    # Comparación
    path('comparar/', views.comparar_clientes, name='comparar_clientes'),
    path('comparar/datos/', views.datos_comparacion, name='datos_comparacion'),
]
