from django.contrib import admin
from .models import Programa, Rutina, EjercicioBase

admin.site.register(Programa)
admin.site.register(Rutina)
admin.site.register(EjercicioBase)
