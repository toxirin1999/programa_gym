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
]
