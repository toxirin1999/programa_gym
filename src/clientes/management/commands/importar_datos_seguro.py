# src/clientes/management/commands/importar_datos_seguro.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

class Command(BaseCommand):
    help = 'Importa datos de forma bruta, ignorando la lógica de la aplicación.'

    def add_arguments(self, parser):
        parser.add_argument('fixture_path', type=str, help='La ruta al archivo de fixture JSON.')

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_path = options['fixture_path']
        
        self.stdout.write(self.style.WARNING('--- MODO DE CARGA BRUTA INICIADO ---'))
        self.stdout.write(self.style.WARNING('Se intentará cargar los datos directamente.'))

        try:
            # El comando loaddata se ejecuta dentro de una transacción atómica.
            # Si algo falla, todo se deshace.
            call_command('loaddata', fixture_path, verbosity=2)
            self.stdout.write(self.style.SUCCESS('\n¡DATOS CARGADOS CON ÉXITO EN LA TRANSACCIÓN!'))
            self.stdout.write(self.style.SUCCESS('Confirmando cambios en la base de datos...'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR DURANTE LOADDATA: {e}'))
            self.stdout.write(self.style.ERROR('La transacción será deshecha. No se guardaron datos.'))
            # Al salir del bloque 'handle' con una excepción, la transacción se revierte.
            raise e # Volvemos a lanzar la excepción para que el Job de Render falle claramente.

        self.stdout.write(self.style.SUCCESS('--- PROCESO FINALIZADO CON ÉXITO ---'))
