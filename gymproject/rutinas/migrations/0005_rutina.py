# Generated by Django 5.2 on 2025-05-10 06:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rutinas', '0004_programa_delete_rutina'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rutina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('programa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rutinas', to='rutinas.programa')),
            ],
        ),
    ]
