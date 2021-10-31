# Generated by Django 3.2.8 on 2021-10-30 00:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apicore', '0007_auto_20211029_2323'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileUserMount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mount', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.datamount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.profileuser')),
            ],
            options={
                'db_table': 'ft_profile_mount',
            },
        ),
    ]
