# Generated by Django 3.1.2 on 2021-09-19 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0003_auto_20210919_0802'),
    ]

    operations = [
        migrations.AlterField(
            model_name='procurementperwarehouse',
            name='procurement',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='procurement.procurement'),
        ),
    ]