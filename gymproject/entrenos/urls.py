from django.urls import path
from .views import entrenos_filtrados
from django.shortcuts import redirect, get_object_or_404
from .models import EntrenoRealizado
from .views import hacer_entreno, empezar_entreno, historial_entrenos
from . import views

urlpatterns = [
    path('hacer/', hacer_entreno, name='hacer_entreno'),
    path('empezar/<int:rutina_id>/', empezar_entreno, name='empezar_entreno'),
    path('entrenos/eliminar/<int:pk>/', views.eliminar_entreno, name='eliminar_entreno'),
    path('entreno-anterior/<int:cliente_id>/<int:rutina_id>/', views.mostrar_entreno_anterior, name='entreno_anterior'),
    path('entrenos/resumen/<int:entreno_id>/', views.resumen_entreno, name='resumen_entreno'),
    
    path('historial/', historial_entrenos, name='historial_entrenos'),  # ✅ nueva ruta
    path('resumen/<str:rango>/', entrenos_filtrados, name='entrenos_filtrados'),

]
