# src/clientes/management/commands/importar_datos_seguro.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from entrenos.models import EntrenoRealizado
from estoico.signals import crear_perfiles_asociados
from analytics.signals import actualizar_metricas_entreno

class Command(BaseCommand):
    help = 'Ejecuta migraciones o carga datos desactivando signals conflictivos.'

    def add_arguments(self, parser):
        parser.add_argument('--migrate-only', action='store_true', help='Solo ejecuta las migraciones.')
        parser.add_argument('--load-data', type=str, help='Ruta al fixture para cargar datos.')

    def handle(self, *args, **options):
        signals_to_disconnect = [
            (crear_perfiles_asociados, User),
            (actualizar_metricas_entreno, EntrenoRealizado),
        ]

        self.stdout.write(self.style.WARNING('--- DESCONECTANDO SIGNALS ---'))
        for signal_func, sender_model in signals_to_disconnect:
            post_save.disconnect(signal_func, sender=sender_model)
        self.stdout.write(self.style.SUCCESS('Signals desconectados.'))

        try:
            if options['migrate_only']:
                self.stdout.write(self.style.WARNING('--- EJECUTANDO MIGRACIONES ---'))
                call_command('migrate')
                self.stdout.write(self.style.SUCCESS('¡Migraciones completadas con éxito!'))
            
            if options['load_data']:
                fixture_path = options['load_data']
                self.stdout.write(self.style.WARNING(f'\n--- INICIANDO LOADDATA PARA {fixture_path} ---'))
                call_command('loaddata', fixture_path)
                self.stdout.write(self.style.SUCCESS('\n¡LOADDATA COMPLETADO CON ÉXITO!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nOcurrió un error: {e}'))
        
        finally:
            self.stdout.write(self.style.WARNING('\n--- RECONECTANDO SIGNALS ---'))
            for signal_func, sender_model in signals_to_disconnect:
                post_save.connect(signal_func, sender=sender_model)
            self.stdout.write(self.style.SUCCESS('Signals reconectados. Proceso finalizado.'))
