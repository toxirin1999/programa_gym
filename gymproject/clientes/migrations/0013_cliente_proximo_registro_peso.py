# Generated by Django 5.2 on 2025-05-14 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0012_dietaasignada'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='proximo_registro_peso',
            field=models.DateField(blank=True, null=True),
        ),
    ]
