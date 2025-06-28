from django.apps import AppConfig

class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clientes.apps'         # Ruta completa del módulo
    label = 'clientes_app'         # Único
