from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

# Asumimos que estos modelos existen en la aplicación
from clientes.models import Cliente
from rutinas.models import Ejercicio
from entrenos.models import EntrenoRealizado, SerieRealizada

class Nivel(models.Model):
    """
    Modelo para definir los niveles del sistema de gamificación.
    Cada nivel requiere una cantidad específica de puntos para ser alcanzado.
    """
    numero = models.PositiveIntegerField(
        primary_key=True,
        verbose_name=_("Número de nivel")
    )
    nombre = models.CharField(
        max_length=50,
        verbose_name=_("Nombre del nivel")
    )
    puntos_requeridos = models.PositiveIntegerField(
        verbose_name=_("Puntos requeridos"),
        help_text=_("Cantidad de puntos necesarios para alcanzar este nivel")
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción")
    )
    icono = models.ImageField(
        upload_to='niveles/',
        blank=True,
        null=True,
        verbose_name=_("Icono")
    )
    
    class Meta:
        verbose_name = _("Nivel")
        verbose_name_plural = _("Niveles")
        ordering = ['numero']
    
    def __str__(self):
        return f"{self.numero} - {self.nombre} ({self.puntos_requeridos} pts)"


class TipoLogro(models.Model):
    """
    Categorías de logros (hitos, consistencia, superación, especiales)
    """
    CATEGORIA_CHOICES = [
        ('hito', _('Hito')),
        ('consistencia', _('Consistencia')),
        ('superacion', _('Superación')),
        ('especial', _('Especial')),
    ]
    
    nombre = models.CharField(
        max_length=50,
        verbose_name=_("Nombre")
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='hito',
        verbose_name=_("Categoría")
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción")
    )
    
    class Meta:
        verbose_name = _("Tipo de Logro")
        verbose_name_plural = _("Tipos de Logros")
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"


class Logro(models.Model):
    """
    Modelo para los logros (badges) que pueden desbloquear los usuarios.
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre")
    )
    descripcion = models.TextField(
        verbose_name=_("Descripción")
    )
    tipo = models.ForeignKey(
        TipoLogro,
        on_delete=models.CASCADE,
        related_name='logros',
        verbose_name=_("Tipo de logro")
    )
    puntos_recompensa = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Puntos de recompensa"),
        help_text=_("Puntos que recibe el usuario al desbloquear este logro")
    )
    icono = models.ImageField(
        upload_to='logros/',
        blank=True,
        null=True,
        verbose_name=_("Icono")
    )
    meta_valor = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Valor meta"),
        help_text=_("Valor numérico que se debe alcanzar para desbloquear el logro")
    )
    es_secreto = models.BooleanField(
        default=False,
        verbose_name=_("Es secreto"),
        help_text=_("Si es verdadero, el logro no se muestra hasta que se desbloquea")
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    class Meta:
        verbose_name = _("Logro")
        verbose_name_plural = _("Logros")
        ordering = ['tipo', 'meta_valor']
    
    def __str__(self):
        return self.nombre


class TipoQuest(models.Model):
    """
    Categorías de misiones (diarias, semanales, mensuales, progresivas)
    """
    PERIODO_CHOICES = [
        ('diaria', _('Diaria')),
        ('semanal', _('Semanal')),
        ('mensual', _('Mensual')),
        ('progresiva', _('Progresiva')),
        ('permanente', _('Permanente')),
    ]
    
    nombre = models.CharField(
        max_length=50,
        verbose_name=_("Nombre")
    )
    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES,
        default='semanal',
        verbose_name=_("Periodo")
    )
    duracion_dias = models.PositiveIntegerField(
        default=7,
        verbose_name=_("Duración en días"),
        help_text=_("Número de días que dura la misión")
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción")
    )
    
    class Meta:
        verbose_name = _("Tipo de Misión")
        verbose_name_plural = _("Tipos de Misiones")
    
    def __str__(self):
        return f"{self.nombre} ({self.get_periodo_display()})"


class Quest(models.Model):
    """
    Modelo para las misiones (quests) que pueden completar los usuarios.
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre")
    )
    descripcion = models.TextField(
        verbose_name=_("Descripción")
    )
    tipo = models.ForeignKey(
        TipoQuest,
        on_delete=models.CASCADE,
        related_name='quests',
        verbose_name=_("Tipo de misión")
    )
    puntos_recompensa = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Puntos de recompensa"),
        help_text=_("Puntos que recibe el usuario al completar esta misión")
    )
    icono = models.ImageField(
        upload_to='quests/',
        blank=True,
        null=True,
        verbose_name=_("Icono")
    )
    meta_valor = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Valor meta"),
        help_text=_("Valor numérico que se debe alcanzar para completar la misión")
    )
    ejercicio = models.ForeignKey(
        Ejercicio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='quests',
        verbose_name=_("Ejercicio relacionado")
    )
    quest_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='quests_hijos',
        verbose_name=_("Misión padre"),
        help_text=_("Para misiones progresivas que forman parte de una serie")
    )
    activa = models.BooleanField(
        default=True,
        verbose_name=_("Activa")
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    class Meta:
        verbose_name = _("Misión")
        verbose_name_plural = _("Misiones")
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        return self.nombre


class PerfilGamificacion(models.Model):
    """
    Perfil de gamificación para cada usuario, con sus puntos, nivel y estadísticas.
    """
    cliente = models.OneToOneField(
        Cliente,
        on_delete=models.CASCADE,
        related_name='perfil_gamificacion',
        verbose_name=_("Cliente")
    )
    puntos_totales = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Puntos totales")
    )
    nivel_actual = models.ForeignKey(
        Nivel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='usuarios',
        verbose_name=_("Nivel actual")
    )
    fecha_ultimo_entreno = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha del último entrenamiento")
    )
    racha_actual = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Racha actual"),
        help_text=_("Días consecutivos de entrenamiento")
    )
    racha_maxima = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Racha máxima"),
        help_text=_("Máximo de días consecutivos de entrenamiento")
    )
    entrenos_totales = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Entrenamientos totales")
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Última actualización")
    )
    
    class Meta:
        verbose_name = _("Perfil de Gamificación")
        verbose_name_plural = _("Perfiles de Gamificación")
    
    def __str__(self):
        return f"Perfil de {self.cliente.nombre} - Nivel {self.nivel_actual.numero if self.nivel_actual else 1}"
    
    def actualizar_nivel(self):
        """Actualiza el nivel del usuario según sus puntos totales"""
        nuevo_nivel = Nivel.objects.filter(
            puntos_requeridos__lte=self.puntos_totales
        ).order_by('-puntos_requeridos').first()
        
        if nuevo_nivel and (not self.nivel_actual or nuevo_nivel.numero > self.nivel_actual.numero):
            self.nivel_actual = nuevo_nivel
            self.save(update_fields=['nivel_actual'])
            return True
        return False


class LogroUsuario(models.Model):
    """
    Relación entre usuarios y logros desbloqueados.
    """
    perfil = models.ForeignKey(
        PerfilGamificacion,
        on_delete=models.CASCADE,
        related_name='logros',
        verbose_name=_("Perfil")
    )
    logro = models.ForeignKey(
        Logro,
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name=_("Logro")
    )
    fecha_desbloqueo = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Fecha de desbloqueo")
    )
    progreso_actual = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Progreso actual")
    )
    completado = models.BooleanField(
        default=False,
        verbose_name=_("Completado")
    )
    
    class Meta:
        verbose_name = _("Logro de Usuario")
        verbose_name_plural = _("Logros de Usuarios")
        unique_together = ('perfil', 'logro')
        ordering = ['-fecha_desbloqueo']
    
    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.logro.nombre}"


class QuestUsuario(models.Model):
    """
    Relación entre usuarios y misiones aceptadas/completadas.
    """
    perfil = models.ForeignKey(
        PerfilGamificacion,
        on_delete=models.CASCADE,
        related_name='quests',
        verbose_name=_("Perfil")
    )
    quest = models.ForeignKey(
        Quest,
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name=_("Misión")
    )
    fecha_inicio = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Fecha de inicio")
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de finalización")
    )
    progreso_actual = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Progreso actual")
    )
    completada = models.BooleanField(
        default=False,
        verbose_name=_("Completada")
    )
    
    class Meta:
        verbose_name = _("Misión de Usuario")
        verbose_name_plural = _("Misiones de Usuarios")
        unique_together = ('perfil', 'quest')
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.quest.nombre}"


class HistorialPuntos(models.Model):
    """
    Registro histórico de puntos ganados por el usuario.
    """
    perfil = models.ForeignKey(
        PerfilGamificacion,
        on_delete=models.CASCADE,
        related_name='historial_puntos',
        verbose_name=_("Perfil")
    )
    puntos = models.PositiveIntegerField(
        verbose_name=_("Puntos")
    )
    entreno = models.ForeignKey(
        EntrenoRealizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos',
        verbose_name=_("Entrenamiento")
    )
    logro = models.ForeignKey(
        Logro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_otorgados',
        verbose_name=_("Logro")
    )
    quest = models.ForeignKey(
        Quest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_otorgados',
        verbose_name=_("Misión")
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Descripción")
    )
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Fecha")
    )
    
    class Meta:
        verbose_name = _("Historial de Puntos")
        verbose_name_plural = _("Historial de Puntos")
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.puntos} pts - {self.fecha.strftime('%d/%m/%Y')}"
