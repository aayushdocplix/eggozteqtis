# Generated by Django 3.1.2 on 2021-09-26 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
        ('procurement', '0015_auto_20210925_1852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batchperwarehouse',
            name='warehouse',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, to='warehouse.warehouse'),
        ),
    ]