# logros/migrations/000X_crear_logros_iniciales.py

from django.db import migrations


def crear_logros_iniciales(apps, schema_editor):
    """
    Crea los objetos Logro iniciales en la base de datos.
    """
    # Obtenemos los modelos de la versión histórica de la app
    Logro = apps.get_model('logros', 'Logro')
    TipoLogro = apps.get_model('logros', 'TipoLogro')

    # --- Crear Tipos de Logro ---
    tipo_liftin, _ = TipoLogro.objects.get_or_create(
        nombre="Liftin",
        defaults={'categoria': 'especial', 'descripcion': 'Logros relacionados con la app Liftin'}
    )
    tipo_superacion, _ = TipoLogro.objects.get_or_create(
        nombre="Superación",
        defaults={'categoria': 'superacion', 'descripcion': 'Logros por superar marcas personales'}
    )
    tipo_consistencia, _ = TipoLogro.objects.get_or_create(
        nombre="Consistencia",
        defaults={'categoria': 'consistencia', 'descripcion': 'Logros por entrenar de forma consistente'}
    )

    # --- Lista de Logros a Crear ---
    logros_a_crear = [
        # Logros de Liftin
        {"nombre": "Liftin Principiante", "descripcion": "Importa 5 entrenamientos desde Liftin.", "tipo": tipo_liftin,
         "puntos_recompensa": 150, "meta_valor": 5},
        {"nombre": "Liftin Intermedio", "descripcion": "Importa 15 entrenamientos desde Liftin.", "tipo": tipo_liftin,
         "puntos_recompensa": 300, "meta_valor": 15},
        {"nombre": "Liftin Avanzado", "descripcion": "Importa 30 entrenamientos desde Liftin.", "tipo": tipo_liftin,
         "puntos_recompensa": 500, "meta_valor": 30},

        # Logros de Calorías
        {"nombre": "Quemador Principiante", "descripcion": "Quema un total de 3000 calorías.", "tipo": tipo_superacion,
         "puntos_recompensa": 100, "meta_valor": 3000},
        {"nombre": "Incinerador", "descripcion": "Quema un total de 10000 calorías.", "tipo": tipo_superacion,
         "puntos_recompensa": 400, "meta_valor": 10000},

        # Logros de Racha
        {"nombre": "Racha de 7 Días", "descripcion": "Entrena 7 días seguidos.", "tipo": tipo_consistencia,
         "puntos_recompensa": 200, "meta_valor": 7},
        {"nombre": "Racha de 30 Días", "descripcion": "Entrena 30 días seguidos. ¡Hábito de hierro!",
         "tipo": tipo_consistencia, "puntos_recompensa": 1000, "meta_valor": 30},
    ]

    # --- Bucle para crear los logros ---
    for data_logro in logros_a_crear:
        # Usamos get_or_create para no duplicar si ya existen
        Logro.objects.get_or_create(
            nombre=data_logro["nombre"],
            defaults=data_logro
        )
    print("\n   -> Logros iniciales creados o verificados.")


class Migration(migrations.Migration):
    dependencies = [
        ('logros', '0001_initial'),  # Asegúrate que el nombre de la migración anterior sea correcto
    ]

    operations = [
        migrations.RunPython(crear_logros_iniciales),
    ]
