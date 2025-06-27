from django.db import models
from django.conf import settings
from rutinas.models import Programa
from rutinas.models import Rutina
from dietas.models import Dieta  # asegúrate de tener esto importado
from django import forms
# En tu archivo models.py (o donde tengas tus modelos)
from django.db import models

# from models import Cliente  # Asegúrate de que tu modelo Cliente esté importado

from django.db import models
from django.contrib.auth.models import User


class SugerenciaAceptada(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    semana_inicio = models.DateField()
    tipo = models.CharField(max_length=20, choices=[
        ('subir', 'Subir carga'),
        ('bajar', 'Bajar carga'),
        ('mantener', 'Mantener carga')
    ])
    aceptada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} ({'✅' if self.aceptada else '❌'})"


class MiniReto(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    semana_inicio = models.DateField()
    descripcion = models.CharField(max_length=200)
    cumplido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.descripcion} ({'✅' if self.cumplido else '❌'})"


class EstadoSemanal(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    semana_inicio = models.DateField()
    semana_fin = models.DateField()
    promedio_sueno = models.DecimalField(max_digits=4, decimal_places=2)
    promedio_rpe = models.DecimalField(max_digits=4, decimal_places=2)
    humor_dominante = models.CharField(max_length=20, choices=[
        ('verde', '😊 Bien'),
        ('amarillo', '😐 Neutro'),
        ('rojo', '😞 Bajo')
    ])
    mensaje_joi = models.TextField(blank=True)
    sugerencia = models.TextField(blank=True, null=True)  # ← AÑADIDO

    def __str__(self):
        return f"Semana {self.semana_inicio} - {self.semana_fin} ({self.cliente})"


class BitacoraDiaria(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    horas_sueno = models.DecimalField(max_digits=4, decimal_places=2)
    humor = models.CharField(max_length=20, choices=[
        ('verde', '😊 Bien'),
        ('amarillo', '😐 Neutro'),
        ('rojo', '😞 Bajo')
    ])
    rpe = models.PositiveSmallIntegerField(help_text="Esfuerzo percibido (1-10)")
    nota_personal = models.TextField(blank=True)
    mindfulness_am = models.BooleanField(default=False)
    mindfulness_pm = models.BooleanField(default=False)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    energia_subjetiva = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Energía subjetiva de 0 a 10")
    dolor_articular = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Dolor articular de 0 a 10")
    autoconciencia = models.TextField(null=True, blank=True, help_text="¿Qué emoción domina (0-10)?")
    descarga_cognitiva = models.TextField(null=True, blank=True, help_text="Escribe 5’ “lo que me preocupa AHORA”")
    rumiacion_baja = models.BooleanField(null=True, blank=True, help_text="¿La rumiación bajó después de escribir?")
    circunferencia_biceps = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    emocion_dia = models.CharField(max_length=100, blank=True)
    cosas_positivas = models.TextField(blank=True, help_text="Escribe 3 cosas que funcionaron hoy.")
    aprendizaje = models.TextField(blank=True)
    # Quién quiero ser hoy
    quien_quiero_ser = models.TextField(blank=True, help_text="Describe qué tipo de persona quieres ser hoy.")

    # Lista de tareas del día (como texto plano)
    tareas_dia = models.TextField(blank=True,
                                  help_text="Escribe hasta 5 tareas importantes para hoy, separadas por saltos de línea.")

    # Mejora del día
    que_puedo_mejorar = models.TextField(blank=True, help_text="Reflexiona sobre qué podrías mejorar del día.")

    # Reflexión final
    reflexion_diaria = models.TextField(blank=True, help_text="Escribe una reflexión libre sobre tu día.")

    limito_socialmente = models.BooleanField(null=True, help_text="¿Respondiste solo, sin iniciar?")

    check_in_energia = models.CharField(max_length=10, choices=[
        ('si', 'Sí, doy más de lo que recibo'),
        ('no', 'No, está equilibrado'),
        ('duda', 'No estoy seguro/a')
    ], blank=True, null=True)

    def __str__(self):
        return f"{self.cliente} - {self.fecha}"


class DietaAsignada(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='dietas_asignadas_clientes')

    dieta = models.ForeignKey(Dieta, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.dieta.nombre} ({self.fecha_inicio})"


class ObjetivoCliente(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='objetivos')
    medida = models.CharField(max_length=20, choices=[
        ('peso', 'Peso (kg)'),
        ('grasa', 'Grasa corporal (%)'),
        ('cintura', 'Cintura (cm)'),
    ])
    valor = models.FloatField()
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'medida')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.get_medida_display()}: {self.valor}"


class RevisionProgreso(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='revisiones')
    fecha = models.DateField(auto_now_add=True)
    peso_corporal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grasa_corporal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cintura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pecho = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    biceps = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    muslos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    hombro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cuello = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    antebrazos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    caderas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gemelos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['fecha']

    def check_alerts(self):
        alertas = []
        if self.grasa_corporal and self.grasa_corporal > 30:
            alertas.append("Grasa corporal alta")
        if self.peso_corporal and self.peso_corporal < 50:
            alertas.append("Peso corporal muy bajo")
        return alertas if alertas else None

    def __str__(self):
        return f"{self.cliente.nombre} - {self.fecha}"


class Cliente(models.Model):
    # --- AÑADE ESTA LÍNEA para vincular Cliente con el usuario de Django ---
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente_perfil',
                                null=True, blank=True)
    # ---------------------------------------------------------------------

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    genero = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Femenino')], blank=True)
    programa = models.ForeignKey(Programa, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ nuevo campo
    rutina_actual = models.ForeignKey(Rutina, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateField(auto_now_add=True)
    membresia_activa = models.BooleanField(default=True)
    fecha_vencimiento_membresia = models.DateField(null=True, blank=True)
    proximo_registro_peso = models.DateField(null=True, blank=True)

    # Campos físicos
    peso_corporal = models.FloatField(null=True, blank=True, help_text="kg")
    grasa_corporal = models.FloatField(null=True, blank=True, help_text="%")
    cintura = models.FloatField(null=True, blank=True, help_text="cm")
    pecho = models.FloatField(null=True, blank=True, help_text="cm")
    hombro = models.FloatField(null=True, blank=True, help_text="cm")
    cuello = models.FloatField(null=True, blank=True, help_text="cm")
    biceps = models.FloatField(null=True, blank=True, help_text="cm")
    antebrazos = models.FloatField(null=True, blank=True, help_text="cm")
    caderas = models.FloatField(null=True, blank=True, help_text="cm")
    muslos = models.FloatField(null=True, blank=True, help_text="cm")
    gemelos = models.FloatField(null=True, blank=True, help_text="cm")
    entrenos_perfectos = models.PositiveIntegerField(default=0)

    # Foto
    foto = models.ImageField(upload_to='clientes_fotos/', null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.nombre}"


class Medida(models.Model):
    nombre = models.CharField(max_length=100)
    valor = models.FloatField(null=True, blank=True)
    unidad = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre}: {self.valor} {self.unidad}"


class PlanNutricional(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='planes_nutricionales')
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    edad = models.IntegerField()
    genero = models.CharField(max_length=1)  # 'M' o 'F'
    altura_cm = models.DecimalField(max_digits=5, decimal_places=2)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    nivel_actividad = models.CharField(max_length=20)
    objetivo = models.CharField(max_length=20)

    calorias_estimadas = models.DecimalField(max_digits=7, decimal_places=2)
    gramos_proteinas = models.DecimalField(max_digits=7, decimal_places=2)
    gramos_grasas = models.DecimalField(max_digits=7, decimal_places=2)
    gramos_carbohidratos = models.DecimalField(max_digits=7, decimal_places=2)

    plan_generado_texto = models.TextField()  # Para guardar el texto completo del plan de la IA

    # Puedes añadir más campos para el plan detallado si la IA lo genera estructurado
    # desayuno = models.TextField(blank=True, null=True)
    # almuerzo = models.TextField(blank=True, null=True)
    # cena = models.TextField(blank=True, null=True)
    # snacks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Plan nutricional para {self.cliente.nombre} - {self.objetivo} ({self.fecha_generacion.strftime('%Y-%m-%d')})"


from django.db import models
from django.conf import settings  # Necesario para settings.AUTH_USER_MODEL


# from django.contrib.auth.models import User # También podrías importar User directamente

# ... tus otras clases de modelo (DietaAsignada, ObjetivoCliente, RevisionProgreso, Cliente, Medida, PlanNutricional) ...

# AÑADE ESTA CLASE UserProfile SI ES TU INTENCIÓN TENERLA
class UserProfile(models.Model):
    # Relación uno a uno con el modelo de usuario de Django
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_profile')

    # Añade aquí otros campos específicos del perfil de usuario si los tienes
    # Por ejemplo:
    # avatar = models.ImageField(upload_to='user_avatars/', null=True, blank=True)
    # bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
