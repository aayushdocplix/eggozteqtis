# Generated by Django 3.1.2 on 2021-10-05 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0019_auto_20210930_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='sku',
            field=models.IntegerField(default=6),
        ),
    ]