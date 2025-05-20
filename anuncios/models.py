from django.db import models


class Anuncio(models.Model):
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
