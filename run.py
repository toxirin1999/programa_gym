# run.py
from whitenoise import WhiteNoise
from gymproject.wsgi import application  # Asegúrate de que 'gymproject' es el nombre de tu carpeta de settings

# El nombre 'application' es el estándar que Gunicorn busca.
# WhiteNoise "envuelve" tu aplicación para servir archivos estáticos.
application = WhiteNoise(application)
