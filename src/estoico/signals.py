from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

# Importa TODOS los modelos que deben crearse junto con un User
from .models import PerfilEstoico, EstadisticaUsuario, ConfiguracionNotificacion
from clientes.models import Cliente  # ¡Importante! También importamos el modelo Cliente

@receiver(post_save, sender=User)
def crear_perfiles_asociados(sender, instance, created, **kwargs):
    # Si la función se llama durante loaddata (raw=True), no hagas nada.
    if kwargs.get('raw', False):
        return

    if created:
        # Usamos get_or_create para más seguridad, aunque con la condición 'raw' ya no sería estrictamente necesario.
        PerfilEstoico.objects.get_or_create(usuario=instance)
        EstadisticaUsuario.objects.get_or_create(usuario=instance)
        ConfiguracionNotificacion.objects.get_or_create(usuario=instance)
        
        # Para Cliente, también usamos get_or_create
        cliente, created_cliente = Cliente.objects.get_or_create(
            user=instance,
            defaults={'nombre': instance.username, 'email': instance.email}
        )

        if created_cliente:
            print(f"✅ Perfil de Cliente creado para el nuevo usuario: {instance.username}")


