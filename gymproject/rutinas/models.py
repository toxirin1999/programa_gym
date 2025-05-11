from django.apps import apps
from django.db import models


class Asignacion(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    programa = models.ForeignKey('rutinas.Programa', on_delete=models.CASCADE)


class Programa(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


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
