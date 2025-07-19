# create_or_update_user.py (VERSIÓN CORREGIDA)
import os
import django

# --- ¡CONFIGURA TUS DATOS AQUÍ! ---
USERNAME = "kure"
PASSWORD = "1234" 
EMAIL = "kure@example.com"
# ------------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

user, created = User.objects.get_or_create(username=USERNAME)

if created:
    user.email = EMAIL
    print(f"Usuario '{USERNAME}' creado.")
else:
    print(f"Usuario '{USERNAME}' ya existía. Actualizando permisos y contraseña.")

# --- ¡CAMBIO IMPORTANTE! ---
# Movemos estos permisos fuera del 'if' para que se apliquen SIEMPRE.
user.is_staff = True
user.is_superuser = True
user.set_password(PASSWORD)
user.save() # Guardamos todos los cambios

print(f"Permisos y contraseña para '{USERNAME}' establecidos correctamente.")
print("¡Proceso completado!")
