# Generated by Django 3.1.2 on 2021-09-24 21:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0009_batchmodel_egg_ph'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eggcleaning',
            old_name='intact',
            new_name='egg_count',
        ),
        migrations.RemoveField(
            model_name='eggcleaning',
            name='egg_type',
        ),
    ]