from django.contrib import admin
from .models import (
    Nivel, TipoLogro, Logro, TipoQuest, Quest,
    PerfilGamificacion, LogroUsuario, QuestUsuario, HistorialPuntos
)


@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'puntos_requeridos')
    search_fields = ('nombre',)
    ordering = ('numero',)


@admin.register(TipoLogro)
class TipoLogroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nombre',)


@admin.register(Logro)
class LogroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'puntos_recompensa', 'es_secreto')
    list_filter = ('tipo', 'es_secreto')
    search_fields = ('nombre', 'descripcion')


@admin.register(TipoQuest)
class TipoQuestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'periodo', 'duracion_dias')
    list_filter = ('periodo',)
    search_fields = ('nombre',)


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'puntos_recompensa', 'activa')
    list_filter = ('tipo', 'activa')
    search_fields = ('nombre', 'descripcion')
    raw_id_fields = ('ejercicio', 'quest_padre')


@admin.register(PerfilGamificacion)
class PerfilGamificacionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'puntos_totales', 'nivel_actual', 'racha_actual')
    search_fields = ('cliente__nombre',)
    raw_id_fields = ('cliente', 'nivel_actual')


@admin.register(LogroUsuario)
class LogroUsuarioAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'logro', 'fecha_desbloqueo', 'completado')
    list_filter = ('completado',)
    search_fields = ('perfil__cliente__nombre', 'logro__nombre')
    raw_id_fields = ('perfil', 'logro')


@admin.register(QuestUsuario)
class QuestUsuarioAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'quest', 'fecha_inicio', 'fecha_fin', 'completada')
    list_filter = ('completada',)
    search_fields = ('perfil__cliente__nombre', 'quest__nombre')
    raw_id_fields = ('perfil', 'quest')


@admin.register(HistorialPuntos)
class HistorialPuntosAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'puntos', 'fecha', 'descripcion')
    search_fields = ('perfil__cliente__nombre', 'descripcion')
    raw_id_fields = ('perfil', 'entreno', 'logro', 'quest')
