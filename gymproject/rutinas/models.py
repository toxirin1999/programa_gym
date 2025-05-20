from django.apps import apps
from django.db import models
from django.db import models


class Asignacion(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    programa = models.ForeignKey('rutinas.Programa', on_delete=models.CASCADE)


from django.db import models


class Programa(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=100, blank=True, null=True)  # nombre del archivo de imagen
    tipo = models.CharField(max_length=50, blank=True, null=True)
    fecha_creacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class EjercicioEnRutina(models.Model):
    rutina = models.ForeignKey('Rutina', on_delete=models.CASCADE, related_name='ejercicios_asignados')
    ejercicio = models.ForeignKey('Ejercicio', on_delete=models.CASCADE)
    orden = models.PositiveIntegerField(default=0)

    series_default = models.PositiveIntegerField(default=3)
    repeticiones_default = models.PositiveIntegerField(default=10)
    peso_default = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('rutina', 'ejercicio')
        ordering = ['orden']

    def __str__(self):
        return f"{self.rutina.nombre} - {self.ejercicio.nombre}"


class Ejercicio(models.Model):
    nombre = models.CharField(max_length=100)
    grupo_muscular = models.CharField(max_length=100)
    equipo = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Rutina(models.Model):
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name='rutinas')
    nombre = models.CharField(max_length=100)
    ejercicios = models.ManyToManyField('Ejercicio', through='RutinaEjercicio')
    orden = models.PositiveIntegerField(default=0)  # ✅ nuevo campo

    def __str__(self):
        return self.nombre


class RutinaEjercicio(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    series = models.PositiveIntegerField()
    repeticiones = models.PositiveIntegerField()
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # NUEVO CAMPO

    def __str__(self):
        return f"{self.ejercicio.nombre} ({self.series}x{self.repeticiones}, {self.peso_kg} kg)"
