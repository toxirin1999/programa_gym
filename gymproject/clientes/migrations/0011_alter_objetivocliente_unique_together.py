# Generated by Django 5.2 on 2025-05-13 17:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0010_alter_revisionprogreso_options_objetivocliente'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='objetivocliente',
            unique_together={('cliente', 'medida')},
        ),
    ]
