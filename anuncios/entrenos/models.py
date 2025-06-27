# Archivo: entrenos/models.py - VERSIÓN COMPLETA CON TODOS LOS CAMPOS DE LIFTIN

from django.db import models
from clientes.models import Cliente
from rutinas.models import Ejercicio, Rutina
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class EntrenoRealizado(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    procesado_gamificacion = models.BooleanField(default=False)

    # ⭐ CAMPOS BÁSICOS DE LIFTIN ⭐
    fuente_datos = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('liftin', 'Liftin'),
        ],
        default='manual',
        help_text="Origen de los datos del entrenamiento"
    )

    liftin_workout_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID único del entrenamiento en Liftin"
    )

    # ⭐ CAMPOS DETALLADOS DE TIEMPO ⭐
    hora_inicio = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de inicio del entrenamiento (ej: 09:43)"
    )

    hora_fin = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de finalización del entrenamiento (ej: 10:46)"
    )

    duracion_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duración total del entrenamiento en minutos"
    )

    tiempo_total_formateado = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Tiempo total como aparece en Liftin (ej: 1:02:23)"
    )

    # ⭐ CAMPOS DE EJERCICIOS Y VOLUMEN ⭐
    numero_ejercicios = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número total de ejercicios realizados"
    )

    volumen_total_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Volumen total levantado en kg (ej: 19000.00 para 19K KG)"
    )

    volumen_total_formateado = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Volumen como aparece en Liftin (ej: 19K KG)"
    )

    # ⭐ CAMPOS DE SALUD Y RENDIMIENTO ⭐
    calorias_quemadas = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calorías quemadas durante el entrenamiento"
    )

    frecuencia_cardiaca_promedio = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Frecuencia cardíaca promedio en BPM"
    )

    frecuencia_cardiaca_maxima = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Frecuencia cardíaca máxima en BPM"
    )

    # ⭐ CAMPOS DE METADATOS ⭐
    nombre_rutina_liftin = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Nombre de la rutina como aparece en Liftin (ej: Día 6 - Full Body)"
    )

    notas_liftin = models.TextField(
        null=True,
        blank=True,
        help_text="Notas adicionales importadas de Liftin"
    )

    fecha_importacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de importación desde Liftin"
    )

    def __str__(self):
        fuente = "📱 Liftin" if self.fuente_datos == 'liftin' else "✏️ Manual"
        rutina_nombre = self.nombre_rutina_liftin or self.rutina.nombre
        return f"{fuente} - {self.cliente.nombre} - {rutina_nombre} ({self.fecha})"

    @property
    def es_de_liftin(self):
        """Método para verificar si el entrenamiento viene de Liftin"""
        return self.fuente_datos == 'liftin'

    @property
    def duracion_formateada(self):
        """Devuelve la duración en formato legible"""
        if self.tiempo_total_formateado:
            return self.tiempo_total_formateado
        elif self.duracion_minutos:
            horas = self.duracion_minutos // 60
            minutos = self.duracion_minutos % 60
            if horas > 0:
                return f"{horas}h {minutos}m"
            return f"{minutos}m"
        return "No especificada"

    @property
    def horario_entrenamiento(self):
        """Devuelve el horario del entrenamiento"""
        if self.hora_inicio and self.hora_fin:
            return f"{self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"
        return "No especificado"

    @property
    def volumen_formateado(self):
        """Devuelve el volumen en formato legible"""
        if self.volumen_total_formateado:
            return self.volumen_total_formateado
        elif self.volumen_total_kg:
            if self.volumen_total_kg >= 1000:
                return f"{self.volumen_total_kg / 1000:.1f}K KG"
            return f"{self.volumen_total_kg} KG"
        return "No especificado"

    class Meta:
        ordering = ['-fecha', '-hora_inicio']
        verbose_name = "Entrenamiento Realizado"
        verbose_name_plural = "Entrenamientos Realizados"


class EjercicioLiftinDetallado(models.Model):
    """
    Modelo para almacenar los ejercicios específicos de Liftin con todos sus detalles
    """
    entreno = models.ForeignKey('EntrenoRealizado', on_delete=models.CASCADE,
                                related_name='ejercicios_liftin_detallados')

    # Información del ejercicio
    nombre_ejercicio = models.CharField(
        max_length=200,
        help_text="Nombre del ejercicio como aparece en Liftin"
    )

    orden_ejercicio = models.PositiveIntegerField(
        default=1,
        help_text="Orden del ejercicio en la rutina"
    )

    # Peso utilizado
    peso_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Peso utilizado en kg"
    )

    peso_formateado = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Peso como aparece en Liftin (ej: 268.5 kg, PC, 90-100 kg)"
    )

    # Series y repeticiones
    series_realizadas = models.PositiveIntegerField(
        default=1,
        help_text="Número de series realizadas"
    )

    repeticiones_formateado = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Repeticiones como aparecen en Liftin (ej: 3x5-10, 3x10-12)"
    )

    repeticiones_min = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Repeticiones mínimas por serie"
    )

    repeticiones_max = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Repeticiones máximas por serie"
    )

    # Estado del ejercicio
    completado = models.BooleanField(
        default=True,
        help_text="Si el ejercicio fue completado exitosamente"
    )

    estado_liftin = models.CharField(
        max_length=20,
        choices=[
            ('completado', '✓ Completado'),
            ('fallado', '✗ Fallado'),
            ('nuevo', 'N Nuevo'),
            ('parcial', '~ Parcial'),
        ],
        default='completado',
        help_text="Estado del ejercicio según Liftin"
    )

    # Notas específicas del ejercicio
    notas_ejercicio = models.TextField(
        null=True,
        blank=True,
        help_text="Notas específicas de este ejercicio"
    )

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        peso_str = self.peso_formateado or f"{self.peso_kg} kg" if self.peso_kg else "Sin peso"
        reps_str = self.repeticiones_formateado or f"{self.repeticiones_min}-{self.repeticiones_max}" if self.repeticiones_min else "Sin reps"
        return f"{self.nombre_ejercicio}: {peso_str}, {reps_str}"

    @property
    def volumen_ejercicio(self):
        """Calcula el volumen aproximado de este ejercicio"""
        if self.peso_kg and self.series_realizadas and self.repeticiones_min:
            # Usar repeticiones promedio si hay rango
            reps_promedio = self.repeticiones_min
            if self.repeticiones_max:
                reps_promedio = (self.repeticiones_min + self.repeticiones_max) / 2

            return self.peso_kg * self.series_realizadas * reps_promedio
        return 0

    class Meta:
        ordering = ['entreno', 'orden_ejercicio']
        verbose_name = "Ejercicio Detallado de Liftin"
        verbose_name_plural = "Ejercicios Detallados de Liftin"


# Mantener modelos existentes para compatibilidad
class DetalleEjercicioRealizado(models.Model):
    entreno = models.ForeignKey(EntrenoRealizado, on_delete=models.CASCADE, related_name='detalles')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    series = models.PositiveIntegerField()
    repeticiones = models.PositiveIntegerField()
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    completado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.ejercicio.nombre}: {self.series}x{self.repeticiones} - {self.peso_kg} kg"


class SerieRealizada(models.Model):
    entreno = models.ForeignKey('EntrenoRealizado', on_delete=models.CASCADE, related_name='series')
    ejercicio = models.ForeignKey('rutinas.Ejercicio', on_delete=models.CASCADE)
    serie_numero = models.PositiveIntegerField()
    repeticiones = models.PositiveIntegerField()
    completado = models.BooleanField(default=False)
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.ejercicio.nombre}: Serie {self.serie_numero} - {self.repeticiones} reps @ {self.peso_kg} kg"


class Rutina(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Programa(models.Model):
    nombre = models.CharField(max_length=100)
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class PlanPersonalizado(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    ejercicio = models.ForeignKey('rutinas.Ejercicio', on_delete=models.CASCADE)
    rutina = models.ForeignKey('rutinas.Rutina', on_delete=models.CASCADE, null=True, blank=True)
    repeticiones_objetivo = models.PositiveIntegerField(default=10)
    peso_objetivo = models.FloatField(default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cliente', 'ejercicio', 'rutina')

    def __str__(self):
        return f"{self.cliente} - {self.ejercicio} → {self.repeticiones_objetivo} reps @ {self.peso_objetivo} kg"


class LogroDesbloqueado(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.nombre}"


# ⭐ MODELO PARA DATOS ESPECÍFICOS DE LIFTIN ⭐
class DatosLiftinDetallados(models.Model):
    """
    Modelo para almacenar datos específicos de Liftin que no encajan
    en la estructura estándar de entrenamientos
    """
    entreno = models.OneToOneField(
        EntrenoRealizado,
        on_delete=models.CASCADE,
        related_name='datos_liftin'
    )

    # Datos de frecuencia cardíaca detallados
    datos_frecuencia_cardiaca = models.JSONField(
        null=True,
        blank=True,
        help_text="Array de datos de frecuencia cardíaca con timestamps"
    )

    # Metadatos de Liftin
    version_liftin = models.CharField(max_length=20, null=True, blank=True)
    dispositivo_origen = models.CharField(max_length=50, null=True, blank=True)

    # Datos de Apple Health/HealthKit
    sincronizado_health = models.BooleanField(default=False)
    health_workout_uuid = models.CharField(max_length=100, null=True, blank=True)

    # Datos adicionales en formato JSON
    metadatos_adicionales = models.JSONField(
        null=True,
        blank=True,
        help_text="Otros datos específicos de Liftin en formato JSON"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Datos Liftin - {self.entreno}"

    class Meta:
        verbose_name = "Datos Detallados de Liftin"
        verbose_name_plural = "Datos Detallados de Liftin"


# Modelo para compatibilidad si es necesario
class EstadoEmocional(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado Emocional"
        verbose_name_plural = "Estados Emocionales"


# 🔧 CAMBIO MÍNIMO 1: AGREGAR AL FINAL DE models.py

# ============================================================================
# AGREGAR ESTE CÓDIGO AL FINAL DE TU ARCHIVO entrenos/models.py
# ============================================================================

class EjercicioLiftin(models.Model):
    """
    Modelo simple para guardar ejercicios individuales de Liftin
    """
    entreno = models.ForeignKey('EntrenoRealizado', on_delete=models.CASCADE, related_name='ejercicios_liftin')

    # Información básica del ejercicio
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre del ejercicio (ej: Prensa, Curl Femoral Tumbado)"
    )

    orden = models.PositiveIntegerField(
        default=1,
        help_text="Orden del ejercicio en la rutina"
    )

    # Peso y repeticiones como aparecen en Liftin
    peso_texto = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Peso como aparece en Liftin (ej: 268.5 kg, PC, 90-100 kg)"
    )

    repeticiones_texto = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Repeticiones como aparecen en Liftin (ej: 3x5-10, 3x10-12)"
    )

    # Estado del ejercicio
    estado = models.CharField(
        max_length=20,
        choices=[
            ('completado', '✓ Completado'),
            ('fallado', '✗ Fallado'),
            ('nuevo', 'N Nuevo'),
            ('parcial', '~ Parcial'),
        ],
        default='completado'
    )

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}: {self.peso_texto}, {self.repeticiones_texto}"

    class Meta:
        ordering = ['entreno', 'orden']
        verbose_name = "Ejercicio de Liftin"
        verbose_name_plural = "Ejercicios de Liftin"


# ============================================================================
# TAMBIÉN AGREGAR ESTA FUNCIÓN HELPER AL FINAL
# ============================================================================

def activar_logros_liftin(entreno):
    """
    Función simple para activar logros basados en datos de Liftin
    """
    from logros.models import LogroDesbloqueado

    cliente = entreno.cliente
    logros_nuevos = []

    # Logro: Primera importación de Liftin
    if not LogroDesbloqueado.objects.filter(
            cliente=cliente,
            nombre="Primera Importación Liftin"
    ).exists():
        logro = LogroDesbloqueado.objects.create(
            cliente=cliente,
            nombre="Primera Importación Liftin",
            descripcion="¡Has importado tu primer entrenamiento desde Liftin!"
        )
        logros_nuevos.append(logro)

    # Logro: Entrenamiento de más de 1 hora
    if entreno.duracion_minutos and entreno.duracion_minutos >= 60:
        if not LogroDesbloqueado.objects.filter(
                cliente=cliente,
                nombre="Entrenamiento Maratón"
        ).exists():
            logro = LogroDesbloqueado.objects.create(
                cliente=cliente,
                nombre="Entrenamiento Maratón",
                descripcion="¡Has completado un entrenamiento de más de 1 hora!"
            )
            logros_nuevos.append(logro)

    # Logro: Más de 300 calorías
    if entreno.calorias_quemadas and entreno.calorias_quemadas >= 300:
        if not LogroDesbloqueado.objects.filter(
                cliente=cliente,
                nombre="Quemador de Calorías"
        ).exists():
            logro = LogroDesbloqueado.objects.create(
                cliente=cliente,
                nombre="Quemador de Calorías",
                descripcion="¡Has quemado más de 300 calorías en un entrenamiento!"
            )
            logros_nuevos.append(logro)

    # Logro: Volumen alto (más de 10K kg)
    if entreno.volumen_total_kg and entreno.volumen_total_kg >= 10000:
        if not LogroDesbloqueado.objects.filter(
                cliente=cliente,
                nombre="Levantador Pesado"
        ).exists():
            logro = LogroDesbloqueado.objects.create(
                cliente=cliente,
                nombre="Levantador Pesado",
                descripcion="¡Has levantado más de 10,000 kg en un entrenamiento!"
            )
            logros_nuevos.append(logro)

    return logros_nuevos


# models.py

class RegistroWhoop(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)  # o Cliente si tienes modelo propio
    fecha = models.DateField(default=timezone.now)
    strain = models.DecimalField(max_digits=4, decimal_places=1)
    recovery = models.PositiveSmallIntegerField(help_text="Porcentaje")
    horas_sueno = models.DurationField()
    rhr = models.PositiveIntegerField(null=True, blank=True)  # Frecuencia cardíaca en reposo
    hrv = models.PositiveIntegerField(null=True, blank=True)  # Variabilidad de FC
    sueno_necesario = models.DurationField()
    sleep_performance = models.PositiveSmallIntegerField(help_text="Porcentaje")
    horas_vs_necesidad = models.FloatField(null=True, blank=True)
    regularidad_sueno = models.FloatField(null=True, blank=True)
    eficiencia_sueno = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ['cliente', 'fecha']

    def __str__(self):
        return f"Whoop de {self.cliente} - {self.fecha}"
