from django.apps import AppConfig  # ✅ IMPORTACIÓN NECESARIA

class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clientes'
    label = 'clientes_app'  # ✅ Esto evita el conflicto anterior
