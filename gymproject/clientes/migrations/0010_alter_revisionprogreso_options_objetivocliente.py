# Generated by Django 5.2 on 2025-05-13 17:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0009_revisionprogreso_antebrazos_revisionprogreso_caderas_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='revisionprogreso',
            options={'ordering': ['fecha']},
        ),
        migrations.CreateModel(
            name='ObjetivoCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medida', models.CharField(choices=[('peso', 'Peso (kg)'), ('grasa', 'Grasa corporal (%)'), ('cintura', 'Cintura (cm)')], max_length=20)),
                ('valor', models.FloatField()),
                ('fecha', models.DateField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objetivos', to='clientes.cliente')),
            ],
        ),
    ]
