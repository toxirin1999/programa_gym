# src/clientes/management/commands/importar_datos_seguro.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from entrenos.models import EntrenoRealizado

# --- Nombres de los signals y sus senders ---
SIGNALS_A_DESCONECTAR = [
    ('estoico.signals', 'crear_perfiles_asociados', User),
    ('analytics.signals', 'actualizar_metricas_entreno', EntrenoRealizado),
    # Añade aquí cualquier otro signal que sospeches que da problemas
]

class Command(BaseCommand):
    help = 'Importa datos desactivando TODOS los signals conflictivos de forma segura.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- MODO SEGURO: INICIANDO PROCESO DE IMPORTACIÓN ---'))
        
        # --- Desconexión Segura ---
        disconnected_signals = []
        for module_path, signal_name, sender in SIGNALS_A_DESCONECTAR:
            try:
                # Intentamos importar la función del signal
                module = __import__(module_path, fromlist=[signal_name])
                signal_func = getattr(module, signal_name)
                
                # Desconectamos el signal
                post_save.disconnect(signal_func, sender=sender)
                
                # Guardamos la referencia para reconectarlo después
                disconnected_signals.append((signal_func, sender))
                self.stdout.write(self.style.SUCCESS(f'Signal "{signal_name}" desconectado.'))
            except (ImportError, AttributeError) as e:
                self.stdout.write(self.style.ERROR(f'No se pudo desconectar el signal "{signal_name}": {e}'))

        # --- Ejecución de loaddata ---
        try:
            self.stdout.write(self.style.WARNING('\n--- INICIANDO LOADDATA ---'))
            # Usamos verbosidad 2 para ver qué se está instalando
            call_command('loaddata', 'backup_datos.json', verbosity=2)
            self.stdout.write(self.style.SUCCESS('\n¡LOADDATA COMPLETADO CON ÉXITO!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nOcurrió un error durante loaddata: {e}'))

        # --- Reconexión Segura ---
        finally:
            self.stdout.write(self.style.WARNING('\n--- RECONECTANDO SIGNALS ---'))
            for signal_func, sender in disconnected_signals:
                post_save.connect(signal_func, sender=sender)
                self.stdout.write(self.style.SUCCESS(f'Signal "{signal_func.__name__}" reconectado.'))
            self.stdout.write(self.style.SUCCESS('Proceso finalizado.'))

