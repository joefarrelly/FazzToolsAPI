# Generated by Django 3.2.8 on 2021-10-21 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apicore', '0015_auto_20211021_1950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='altprofession',
            name='profession1',
        ),
        migrations.AddField(
            model_name='altprofession',
            name='profession1',
            field=models.PositiveIntegerField(default=41),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='altprofession',
            name='profession2',
        ),
        migrations.AddField(
            model_name='altprofession',
            name='profession2',
            field=models.PositiveIntegerField(default=124),
            preserve_default=False,
        ),
    ]
