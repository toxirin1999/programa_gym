# logros/models.py

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from clientes.models import Cliente


# --------------------------------------------------------------------------
# MODELOS DEL NUEVO "CÓDICE DE LAS LEYENDAS"
# --------------------------------------------------------------------------

class Arquetipo(models.Model):
    """Representa un Capítulo del Códice, asociado a un personaje y un nivel."""
    nivel = models.PositiveIntegerField(primary_key=True, verbose_name=_("Nivel"))
    nombre_personaje = models.CharField(max_length=100, verbose_name=_("Nombre del Personaje"))
    titulo_arquetipo = models.CharField(max_length=100, verbose_name=_("Título del Arquetipo"))
    filosofia = models.TextField(verbose_name=_("Filosofía del Nivel"))
    puntos_requeridos = models.PositiveIntegerField(verbose_name=_("Puntos Requeridos para Desbloquear"))
    icono_fa = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: 'fas fa-fist-raised'")
    imagen_url = models.URLField(blank=True, null=True, help_text="URL a una imagen épica del personaje.")

    class Meta:
        verbose_name = _("Arquetipo (Nivel)")
        verbose_name_plural = _("Arquetipos (Niveles)")
        ordering = ['nivel']

    def __str__(self):
        return f"Nivel {self.nivel}: {self.titulo_arquetipo}"


class PruebaLegendaria(models.Model):
    """Representa un Logro Épico, que es una prueba dentro de un capítulo/arquetipo."""
    arquetipo = models.ForeignKey(Arquetipo, on_delete=models.CASCADE, related_name='pruebas')
    nombre = models.CharField(max_length=200, verbose_name=_("Nombre de la Prueba"))
    descripcion = models.TextField(verbose_name=_("Descripción"))
    clave_calculo = models.CharField(max_length=50, unique=True, help_text="Identificador para la lógica de cálculo.")
    meta_valor = models.FloatField(default=1.0)
    puntos_recompensa = models.PositiveIntegerField(default=100)
    es_secreta = models.BooleanField(default=False, help_text=_("Oculta hasta ser completada."))

    class Meta:
        verbose_name = _("Prueba Legendaria (Logro)")
        verbose_name_plural = _("Pruebas Legendarias (Logros)")
        ordering = ['arquetipo', 'nombre']

    def __str__(self):
        return f"({self.arquetipo.nombre_personaje}) - {self.nombre}"


class PerfilGamificacion(models.Model):
    """El perfil del cliente. Ahora se relaciona con Arquetipo en lugar de Nivel."""
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
        Arquetipo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfiles',
        verbose_name=_("Arquetipo Actual")
    )
    fecha_ultimo_entreno = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha del último entrenamiento")
    )
    racha_actual = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Racha actual")
    )
    racha_maxima = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Racha máxima")
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
        return f"Perfil de {self.cliente.nombre} - {self.nivel_actual.titulo_arquetipo if self.nivel_actual else 'Nivel Inicial'}"

    def actualizar_nivel(self):
        """Actualiza el nivel (Arquetipo) del usuario según sus puntos totales."""
        nuevo_arquetipo = Arquetipo.objects.filter(
            puntos_requeridos__lte=self.puntos_totales
        ).order_by('-nivel').first()

        if nuevo_arquetipo and (not self.nivel_actual or nuevo_arquetipo.nivel > self.nivel_actual.nivel):
            nivel_anterior = self.nivel_actual
            self.nivel_actual = nuevo_arquetipo
            self.save(update_fields=['nivel_actual'])
            return True
        return False


class PruebaUsuario(models.Model):
    """El progreso de un cliente en una Prueba Legendaria específica."""
    perfil = models.ForeignKey(PerfilGamificacion, on_delete=models.CASCADE, related_name='pruebas_completadas')
    prueba = models.ForeignKey(PruebaLegendaria, on_delete=models.CASCADE)
    progreso_actual = models.FloatField(default=0)
    completada = models.BooleanField(default=False)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Progreso de Prueba de Usuario")
        verbose_name_plural = _("Progresos de Pruebas de Usuarios")
        unique_together = ('perfil', 'prueba')

    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.prueba.nombre}"


# --------------------------------------------------------------------------
# MODELOS DE MISIONES (QUESTS) - SIN CAMBIOS
# --------------------------------------------------------------------------

class TipoQuest(models.Model):
    """Tipos de misiones disponibles"""
    nombre = models.CharField(max_length=50, unique=True, verbose_name=_("Nombre"))
    descripcion = models.TextField(blank=True, verbose_name=_("Descripción"))
    icono = models.CharField(max_length=50, blank=True, verbose_name=_("Icono"))

    class Meta:
        verbose_name = _("Tipo de Quest")
        verbose_name_plural = _("Tipos de Quest")

    def __str__(self):
        return self.nombre


class Quest(models.Model):
    """Misiones que los usuarios pueden completar"""
    PERIODO_CHOICES = [
        ('diario', _('Diario')),
        ('semanal', _('Semanal')),
        ('mensual', _('Mensual')),
        ('especial', _('Especial')),
    ]

    nombre = models.CharField(max_length=200, verbose_name=_("Nombre"))
    descripcion = models.TextField(verbose_name=_("Descripción"))
    tipo = models.ForeignKey(TipoQuest, on_delete=models.CASCADE, verbose_name=_("Tipo"))
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, verbose_name=_("Período"))
    puntos_recompensa = models.PositiveIntegerField(verbose_name=_("Puntos de recompensa"))
    activa = models.BooleanField(default=True, verbose_name=_("Activa"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))

    class Meta:
        verbose_name = _("Quest")
        verbose_name_plural = _("Quests")

    def __str__(self):
        return f"{self.nombre} ({self.get_periodo_display()})"


class QuestUsuario(models.Model):
    """Progreso de un usuario en una quest específica"""
    perfil = models.ForeignKey(PerfilGamificacion, on_delete=models.CASCADE, related_name='quests_usuario')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progreso_actual = models.FloatField(default=0, verbose_name=_("Progreso actual"))
    completada = models.BooleanField(default=False, verbose_name=_("Completada"))
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de inicio"))
    fecha_completada = models.DateTimeField(null=True, blank=True, verbose_name=_("Fecha de completada"))

    class Meta:
        verbose_name = _("Quest de Usuario")
        verbose_name_plural = _("Quests de Usuario")
        unique_together = ('perfil', 'quest')

    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.quest.nombre}"


# --------------------------------------------------------------------------
# MODELOS DE HISTORIAL Y NOTIFICACIONES
# --------------------------------------------------------------------------

class HistorialPuntos(models.Model):
    """Historial de puntos ganados por el usuario"""
    perfil = models.ForeignKey(PerfilGamificacion, on_delete=models.CASCADE, related_name='historial_puntos')
    puntos = models.PositiveIntegerField(verbose_name=_("Puntos"))
    entreno = models.ForeignKey('entrenos.EntrenoRealizado', on_delete=models.SET_NULL, null=True, blank=True)
    prueba_legendaria = models.ForeignKey(PruebaLegendaria, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='puntos_otorgados')
    quest = models.ForeignKey(Quest, on_delete=models.SET_NULL, null=True, blank=True, related_name='puntos_otorgados')
    descripcion = models.CharField(max_length=255, blank=True, verbose_name=_("Descripción"))
    fecha = models.DateTimeField(default=timezone.now, verbose_name=_("Fecha"))

    class Meta:
        verbose_name = _("Historial de Puntos")
        verbose_name_plural = _("Historial de Puntos")
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.puntos} puntos - {self.fecha.strftime('%d/%m/%Y')}"


class Notificacion(models.Model):
    """Notificaciones para el usuario"""
    TIPO_CHOICES = [
        ('logro', _('Logro')),
        ('quest', _('Quest')),
        ('nivel', _('Nivel')),
        ('general', _('General')),
    ]

    perfil = models.ForeignKey(PerfilGamificacion, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name=_("Tipo"))
    titulo = models.CharField(max_length=200, verbose_name=_("Título"))
    mensaje = models.TextField(verbose_name=_("Mensaje"))
    leida = models.BooleanField(default=False, verbose_name=_("Leída"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))

    class Meta:
        verbose_name = _("Notificación")
        verbose_name_plural = _("Notificaciones")
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.perfil.cliente.nombre} - {self.titulo}"
