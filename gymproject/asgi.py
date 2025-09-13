# gymproject/asgi.py
import os
import sys
from django.core.asgi import get_asgi_application

# --- AÑADE ESTAS LÍNEAS ---
# Añade la carpeta raíz del proyecto al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
# -------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')

application = get_asgi_application()
