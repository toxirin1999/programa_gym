# Archivo: entrenos/admin.py - VERSIÓN ACTUALIZADA

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EntrenoRealizado,
    DetalleEjercicioRealizado,
    SerieRealizada,
    DatosLiftinDetallados,
    LogroDesbloqueado
)


@admin.register(EntrenoRealizado)
class EntrenoRealizadoAdmin(admin.ModelAdmin):
    list_display = [
        'cliente',
        'rutina',
        'fecha',
        'fuente_datos_badge',
        'duracion_formateada',
        'calorias_quemadas',
        'frecuencia_cardiaca_promedio',
        'procesado_gamificacion'
    ]

    list_filter = [
        'fuente_datos',
        'fecha',
        'procesado_gamificacion',
        'cliente',
        'rutina'
    ]

    search_fields = [
        'cliente__nombre',
        'rutina__nombre',
        'liftin_workout_id',
        'notas_liftin'
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'rutina', 'fecha')
        }),
        ('Datos de Liftin', {
            'fields': (
                'fuente_datos',
                'liftin_workout_id',
                'duracion_minutos',
                'calorias_quemadas',
                'frecuencia_cardiaca_promedio',
                'frecuencia_cardiaca_maxima',
                'notas_liftin',
                'fecha_importacion'
            ),
            'classes': ('collapse',),
            'description': 'Datos específicos importados desde la aplicación Liftin'
        }),
        ('Sistema', {
            'fields': ('procesado_gamificacion',),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['fecha_importacion']

    def fuente_datos_badge(self, obj):
        """Muestra un badge colorido para la fuente de datos"""
        if obj.fuente_datos == 'liftin':
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">📱 LIFTIN</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✏️ MANUAL</span>'
            )

    fuente_datos_badge.short_description = 'Fuente'

    def duracion_formateada(self, obj):
        """Muestra la duración en formato legible"""
        return obj.duracion_formateada

    duracion_formateada.short_description = 'Duración'

    actions = ['marcar_como_liftin', 'marcar_como_manual']

    def marcar_como_liftin(self, request, queryset):
        """Acción para marcar entrenamientos como provenientes de Liftin"""
        updated = queryset.update(fuente_datos='liftin')
        self.message_user(request, f'{updated} entrenamientos marcados como de Liftin.')

    marcar_como_liftin.short_description = "Marcar como datos de Liftin"

    def marcar_como_manual(self, request, queryset):
        """Acción para marcar entrenamientos como manuales"""
        updated = queryset.update(fuente_datos='manual')
        self.message_user(request, f'{updated} entrenamientos marcados como manuales.')

    marcar_como_manual.short_description = "Marcar como datos manuales"


@admin.register(DetalleEjercicioRealizado)
class DetalleEjercicioRealizadoAdmin(admin.ModelAdmin):
    list_display = [
        'entreno',
        'ejercicio',
        'series',
        'repeticiones',
        'peso_kg',
        'completado'
    ]

    list_filter = [
        'completado',
        'ejercicio',
        'entreno__fuente_datos'
    ]

    search_fields = [
        'ejercicio__nombre',
        'entreno__cliente__nombre'
    ]


@admin.register(SerieRealizada)
class SerieRealizadaAdmin(admin.ModelAdmin):
    list_display = [
        'entreno',
        'ejercicio',
        'serie_numero',
        'repeticiones',
        'peso_kg',
        'completado'
    ]

    list_filter = [
        'completado',
        'ejercicio',
        'entreno__fuente_datos'
    ]

    search_fields = [
        'ejercicio__nombre',
        'entreno__cliente__nombre'
    ]


@admin.register(DatosLiftinDetallados)
class DatosLiftinDetalladosAdmin(admin.ModelAdmin):
    list_display = [
        'entreno',
        'version_liftin',
        'dispositivo_origen',
        'sincronizado_health',
        'fecha_creacion'
    ]

    list_filter = [
        'sincronizado_health',
        'version_liftin',
        'dispositivo_origen',
        'fecha_creacion'
    ]

    search_fields = [
        'entreno__cliente__nombre',
        'health_workout_uuid',
        'version_liftin'
    ]

    fieldsets = (
        ('Entrenamiento Asociado', {
            'fields': ('entreno',)
        }),
        ('Datos de Liftin', {
            'fields': (
                'version_liftin',
                'dispositivo_origen',
                'datos_frecuencia_cardiaca',
                'metadatos_adicionales'
            )
        }),
        ('Sincronización con Apple Health', {
            'fields': (
                'sincronizado_health',
                'health_workout_uuid'
            ),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(LogroDesbloqueado)
class LogroDesbloqueadoAdmin(admin.ModelAdmin):
    list_display = [
        'cliente',
        'nombre',
        'descripcion',
        'fecha'
    ]

    list_filter = [
        'fecha',
        'cliente'
    ]

    search_fields = [
        'cliente__nombre',
        'nombre',
        'descripcion'
    ]


# Personalización del admin site
admin.site.site_header = "Gym Project - Administración"
admin.site.site_title = "Gym Project Admin"
admin.site.index_title = "Panel de Administración del Gimnasio"
