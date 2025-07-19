# create_or_update_user.py
import os
import django

# --- ¡CONFIGURA TUS DATOS AQUÍ! ---
USERNAME = "kure"
PASSWORD = "1234" # Elige una contraseña segura
EMAIL = "kure@example.com" # Puedes poner un email cualquiera
# ------------------------------------

# Configuración de Django para que el script funcione
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Intenta obtener el usuario. Si no existe, lo crea.
user, created = User.objects.get_or_create(username=USERNAME)

if created:
    user.email = EMAIL
    user.is_staff = True  # Para que pueda acceder al panel de admin
    user.is_superuser = True # Para que sea superusuario
    print(f"Usuario '{USERNAME}' creado.")
else:
    print(f"Usuario '{USERNAME}' ya existía. Actualizando contraseña.")

# Establece o actualiza la contraseña
user.set_password(PASSWORD)
user.save()

print(f"Contraseña para '{USERNAME}' establecida correctamente.")
print("¡Proceso completado!")
