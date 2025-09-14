# src/clientes/management/commands/importar_datos_seguro.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from entrenos.models import EntrenoRealizado

# --- IMPORTAMOS LOS DOS SIGNALS CON SUS NOMBRES REALES ---
from estoico.signals import crear_perfiles_asociados
from analytics.signals import actualizar_metricas_entreno # <-- ¡EL NOMBRE REAL Y CORRECTO!

class Command(BaseCommand):
    help = 'Importa datos desactivando TODOS los signals conflictivos.'

    def add_arguments(self, parser):
        parser.add_argument('fixture_path', type=str, help='La ruta al archivo de fixture JSON.')

    def handle(self, *args, **options):
        fixture_path = options['fixture_path']

        self.stdout.write(self.style.WARNING('--- DESCONECTANDO SIGNALS ---'))
        
        # Desconectamos el signal de creación de perfiles de usuario
        post_save.disconnect(crear_perfiles_asociados, sender=User)
        self.stdout.write(self.style.SUCCESS('Signal de creación de perfiles de usuario: DESCONECTADO'))
        
        # --- USAMOS EL NOMBRE REAL PARA DESCONECTAR ---
        post_save.disconnect(actualizar_metricas_entreno, sender=EntrenoRealizado)
        self.stdout.write(self.style.SUCCESS('Signal de métricas de entreno: DESCONECTADO'))

        try:
            self.stdout.write(self.style.WARNING(f'\n--- INICIANDO LOADDATA PARA {fixture_path} ---'))
            call_command('loaddata', fixture_path)
            self.stdout.write(self.style.SUCCESS('\n¡LOADDATA COMPLETADO CON ÉXITO!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nOcurrió un error durante loaddata: {e}'))
        
        finally:
            self.stdout.write(self.style.WARNING('\n--- RECONECTANDO SIGNALS ---'))
            # Volvemos a conectar ambos signals con sus nombres reales
            post_save.connect(crear_perfiles_asociados, sender=User)
            post_save.connect(actualizar_metricas_entreno, sender=EntrenoRealizado)
            self.stdout.write(self.style.SUCCESS('Signals reconectados. Proceso finalizado.'))
