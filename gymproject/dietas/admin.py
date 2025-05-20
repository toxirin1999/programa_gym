from django.contrib import admin
from .models import Dieta, Comida, ClienteDieta


class ComidaInline(admin.TabularInline):
    model = Comida
    extra = 1


class DietaAdmin(admin.ModelAdmin):
    inlines = [ComidaInline]


admin.site.register(Dieta, DietaAdmin)
admin.site.register(ClienteDieta)
