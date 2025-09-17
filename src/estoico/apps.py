# src/estoico/apps.py
import os # <-- AÑADE ESTA LÍNEA
from django.apps import AppConfig

class EstoicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'estoico'

    def ready(self):
        # Si la variable de entorno está presente, NO importes los signals.
        if os.environ.get('DJANGO_IMPORTING_DATA') == 'True':
            return
        
        # Si no, importa los signals como siempre.
        #import estoico.signals 
