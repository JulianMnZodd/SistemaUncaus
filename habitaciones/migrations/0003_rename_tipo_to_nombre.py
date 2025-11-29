# Generated migration to rename tipo field to nombre in Sector model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('habitaciones', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sector',
            old_name='tipo',
            new_name='nombre',
        ),
        migrations.AlterField(
            model_name='sector',
            name='nombre',
            field=models.CharField(max_length=100, verbose_name='Nombre del Sector', db_column='tipo'),
        ),
    ]
