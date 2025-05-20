from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_dietas, name='listar_dietas'),
    path('agregar/', views.agregar_dieta, name='agregar_dieta'),
    path('ver/<int:dieta_id>/', views.ver_dieta, name='ver_dieta'),
    path('editar/<int:dieta_id>/', views.editar_dieta, name='editar_dieta'),
    path('eliminar/<int:dieta_id>/', views.eliminar_dieta, name='eliminar_dieta'),
    path('exportar_pdf/<int:dieta_id>/', views.exportar_dieta_pdf, name='exportar_dieta_pdf'),

    path('dieta/<int:dieta_id>/comidas/nueva/', views.agregar_comida, name='agregar_comida'),
    path('quitar_dieta/<int:cliente_dieta_id>/', views.quitar_dieta, name='quitar_dieta'),

    path('asignar/', views.asignar_dieta, name='asignar_dieta'),
    path('asignar_ajax/', views.asignar_dieta_ajax, name='asignar_dieta_ajax'),
]
