# Generated by Django 3.0.8 on 2020-07-17 13:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20200717_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
