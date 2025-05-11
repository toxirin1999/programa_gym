from django.urls import path
from . import views
from clientes import views as clientes_views

urlpatterns = [
    # Clientes
    path('', views.index, name='clientes_index'),
    path('agregar/', views.agregar_cliente, name='agregar_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('detalle/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('programa/<int:programa_id>/asignar_cliente/', views.asignar_programa_a_cliente,
         name='asignar_programa_a_cliente'),
    path('cliente/<int:cliente_id>/revisiones/', views.lista_revisiones, name='lista_revisiones'),
    path('cliente/<int:cliente_id>/revisiones/agregar/', views.agregar_revision, name='agregar_revision'),
    path('cliente/<int:cliente_id>/asignar_dieta/', views.asignar_dieta_directo, name='asignar_dieta_directo'),
    path('panel/', clientes_views.dashboard, name='dashboard'),
    path('datos-graficas/<int:cliente_id>/', views.datos_graficas, name='datos_graficas'),
    # Medidas (con prefijo para no pisar rutas de clientes)
    path('medidas/', views.lista_medidas, name='lista_medidas'),
    path('medidas/agregar/', views.agregar_medida, name='agregar_medida'),
]
