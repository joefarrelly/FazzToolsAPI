# Generated by Django 3.2.8 on 2021-11-17 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apicore', '0002_profileuser_userlastupdate'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSpell',
            fields=[
                ('spellId', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('spellName', models.CharField(max_length=100)),
                ('spellDescription', models.CharField(max_length=500)),
                ('spellMediaIcon', models.CharField(max_length=150)),
            ],
            options={
                'db_table': 'ft_data_spell',
            },
        ),
    ]
