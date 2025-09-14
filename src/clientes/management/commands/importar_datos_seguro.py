# src/clientes/management/commands/importar_datos_seguro.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User

# ¡IMPORTANTE! Debemos importar la función del signal para poder desconectarla.
# Ajusta la ruta de importación según dónde esté tu archivo de signals.
# Si está en 'estoico/signals.py', sería:
from estoico.signals import crear_perfiles_asociados


class Command(BaseCommand):
    help = 'Importa datos desde un fixture desactivando temporalmente los signals de creación de perfiles.'

    def add_arguments(self, parser):
        parser.add_argument('fixture_path', type=str, help='La ruta al archivo de fixture JSON.')

    def handle(self, *args, **options):
        fixture_path = options['fixture_path']

        self.stdout.write(self.style.WARNING('Desconectando el signal crear_perfiles_asociados...'))
        # Desconectamos el signal del modelo User
        post_save.disconnect(crear_perfiles_asociados, sender=User)

        try:
            self.stdout.write(self.style.SUCCESS(f'Signal desconectado. Iniciando loaddata para {fixture_path}...'))
            # Ejecutamos loaddata. Django se encargará de las migraciones.
            call_command('loaddata', fixture_path)
            self.stdout.write(self.style.SUCCESS('¡loaddata completado con éxito!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error durante loaddata: {e}'))

        finally:
            self.stdout.write(self.style.WARNING('Reconectando el signal crear_perfiles_asociados...'))
            # Volvemos a conectar el signal para que la app funcione normalmente
            post_save.connect(crear_perfiles_asociados, sender=User)
            self.stdout.write(self.style.SUCCESS('Signal reconectado. Proceso finalizado.'))
