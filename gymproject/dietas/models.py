from django.db import models


class Dieta(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    calorias_totales = models.PositiveIntegerField(help_text="Calorías por día (aprox.)")

    def __str__(self):
        return self.nombre


class Comida(models.Model):
    dieta = models.ForeignKey(Dieta, on_delete=models.CASCADE, related_name='comidas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    hora_aproximada = models.TimeField(help_text="Hora sugerida (ej. 08:00 AM)")

    def __str__(self):
        return f"{self.nombre} ({self.dieta.nombre})"


class ClienteDieta(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='dietas_asignadas')
    dieta = models.ForeignKey(Dieta, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.dieta.nombre}"
