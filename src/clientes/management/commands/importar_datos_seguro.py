# src/clientes/management/commands/importar_datos_seguro.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from entrenos.models import EntrenoRealizado # ¡NUEVA IMPORTACIÓN!

# --- IMPORTA AQUÍ TODOS TUS SIGNALS PROBLEMÁTICOS ---
from estoico.signals import crear_perfiles_asociados
# Asumiendo que el nuevo signal está en 'analytics/signals.py' y se llama 'procesar_entreno_gamificacion'
from analytics.signals import procesar_entreno_gamificacion # ¡NUEVA IMPORTACIÓN!

class Command(BaseCommand):
    help = 'Importa datos desactivando TODOS los signals conflictivos.'

    def add_arguments(self, parser):
        parser.add_argument('fixture_path', type=str, help='La ruta al archivo de fixture JSON.')

    def handle(self, *args, **options):
        fixture_path = options['fixture_path']

        self.stdout.write(self.style.WARNING('--- DESCONECTANDO SIGNALS ---'))
        post_save.disconnect(crear_perfiles_asociados, sender=User)
        self.stdout.write(self.style.SUCCESS('Signal de creación de perfiles de usuario: DESCONECTADO'))
        
        # --- DESCONECTAMOS EL SEGUNDO SIGNAL ---
        post_save.disconnect(procesar_entreno_gamificacion, sender=EntrenoRealizado)
        self.stdout.write(self.style.SUCCESS('Signal de gamificación de entrenos: DESCONECTADO'))

        try:
            self.stdout.write(self.style.WARNING(f'\n--- INICIANDO LOADDATA PARA {fixture_path} ---'))
            call_command('loaddata', fixture_path)
            self.stdout.write(self.style.SUCCESS('\n¡LOADDATA COMPLETADO CON ÉXITO!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nOcurrió un error durante loaddata: {e}'))
        
        finally:
            self.stdout.write(self.style.WARNING('\n--- RECONECTANDO SIGNALS ---'))
            post_save.connect(crear_perfiles_asociados, sender=User)
            post_save.connect(procesar_entreno_gamificacion, sender=EntrenoRealizado)
            self.stdout.write(self.style.SUCCESS('Signals reconectados. Proceso finalizado.'))
