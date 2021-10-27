# Generated by Django 3.2.8 on 2021-10-26 18:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataEquipment',
            fields=[
                ('equipmentId', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('equipmentName', models.CharField(max_length=80)),
                ('equipmentType', models.CharField(max_length=20)),
                ('equipmentSlot', models.CharField(max_length=20)),
                ('equipmentIcon', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'ft_data_equipment',
            },
        ),
        migrations.CreateModel(
            name='DataProfession',
            fields=[
                ('professionId', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('professionName', models.CharField(max_length=30)),
                ('professionDescription', models.CharField(max_length=300)),
            ],
            options={
                'db_table': 'ft_data_profession',
            },
        ),
        migrations.CreateModel(
            name='DataProfessionRecipe',
            fields=[
                ('recipeId', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('recipeName', models.CharField(max_length=50)),
                ('recipeDescription', models.CharField(max_length=300)),
                ('recipeCategory', models.CharField(max_length=50)),
                ('recipeRank', models.PositiveSmallIntegerField()),
                ('recipeCraftedQuantity', models.PositiveIntegerField()),
            ],
            options={
                'db_table': 'ft_data_professionrecipe',
            },
        ),
        migrations.CreateModel(
            name='DataProfessionTier',
            fields=[
                ('tierId', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('tierName', models.CharField(max_length=50)),
                ('tierMinSkill', models.PositiveSmallIntegerField()),
                ('tierMaxSkill', models.PositiveSmallIntegerField()),
                ('profession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofession')),
            ],
            options={
                'db_table': 'ft_data_professiontier',
            },
        ),
        migrations.CreateModel(
            name='DataReagent',
            fields=[
                ('reagentId', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('reagentName', models.CharField(max_length=50)),
                ('reagentQuality', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'ft_data_reagent',
            },
        ),
        migrations.CreateModel(
            name='ProfileAlt',
            fields=[
                ('altId', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('altLevel', models.PositiveSmallIntegerField()),
                ('altName', models.CharField(max_length=40)),
                ('altRealm', models.CharField(max_length=40)),
                ('altRealmId', models.PositiveSmallIntegerField()),
                ('altRealmSlug', models.CharField(max_length=40)),
                ('altClass', models.PositiveSmallIntegerField(choices=[(0, 'No Class'), (1, 'Warrior'), (2, 'Paladin'), (3, 'Hunter'), (4, 'Rogue'), (5, 'Priest'), (6, 'Death Knight'), (7, 'Shaman'), (8, 'Mage'), (9, 'Warlock'), (10, 'Monk'), (11, 'Druid'), (12, 'Demon Hunter')], default=0)),
                ('altRace', models.PositiveSmallIntegerField(choices=[(0, 'No Race'), (1, 'Human'), (2, 'Orc'), (3, 'Dwarf'), (4, 'Night Elf'), (5, 'Undead'), (6, 'Tauren'), (7, 'Gnome'), (8, 'Troll'), (9, 'Goblin'), (10, 'Blood Elf'), (11, 'Draenei'), (22, 'Worgen'), (24, 'Pandaren'), (25, 'Pandaren'), (26, 'Pandaren'), (27, 'Nightbourne'), (28, 'Highmountain Tauren'), (29, 'Void Elf'), (30, 'Lightforged Draenei'), (31, 'Zandalari Troll'), (32, 'Kul Tiran'), (34, 'Dark Iron Dwarf'), (35, 'Vulpera'), (36, "Mag'ar Orc"), (37, 'Mechagnome')], default=0)),
                ('altGender', models.CharField(max_length=6)),
                ('altFaction', models.CharField(max_length=10)),
                ('altExpiryDate', models.DateTimeField()),
            ],
            options={
                'db_table': 'ft_profile_alt',
            },
        ),
        migrations.CreateModel(
            name='ProfileFazzToolsUser',
            fields=[
                ('userId', models.CharField(max_length=100, primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'ft_profile_fazztoolsuser',
            },
        ),
        migrations.CreateModel(
            name='ProfileAltEquipment',
            fields=[
                ('alt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='apicore.profilealt')),
                ('head', models.CharField(max_length=40)),
                ('neck', models.CharField(max_length=40)),
                ('shoulder', models.CharField(max_length=40)),
                ('back', models.CharField(max_length=40)),
                ('chest', models.CharField(max_length=40)),
                ('tabard', models.CharField(max_length=40)),
                ('shirt', models.CharField(max_length=40)),
                ('wrist', models.CharField(max_length=40)),
                ('hands', models.CharField(max_length=40)),
                ('belt', models.CharField(max_length=40)),
                ('legs', models.CharField(max_length=40)),
                ('feet', models.CharField(max_length=40)),
                ('ring1', models.CharField(max_length=40)),
                ('ring2', models.CharField(max_length=40)),
                ('trinket1', models.CharField(max_length=40)),
                ('trinket2', models.CharField(max_length=40)),
                ('weapon1', models.CharField(max_length=40)),
                ('weapon2', models.CharField(max_length=40)),
                ('altEquipmentExpiryDate', models.DateTimeField()),
            ],
            options={
                'db_table': 'ft_profile_altequipment',
            },
        ),
        migrations.CreateModel(
            name='ProfileAltProfession',
            fields=[
                ('alt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='apicore.profilealt')),
                ('profession1', models.PositiveIntegerField(choices=[(0, 'Missing'), (171, 'Alchemy'), (164, 'Blacksmithing'), (333, 'Enchanting'), (202, 'Engineering'), (773, 'Inscription'), (755, 'Jewelcrafting'), (165, 'Leatherworking'), (197, 'Tailoring'), (182, 'Herbalism'), (186, 'Mining'), (393, 'Skinning')], default=0)),
                ('profession2', models.PositiveIntegerField(choices=[(0, 'Missing'), (171, 'Alchemy'), (164, 'Blacksmithing'), (333, 'Enchanting'), (202, 'Engineering'), (773, 'Inscription'), (755, 'Jewelcrafting'), (165, 'Leatherworking'), (197, 'Tailoring'), (182, 'Herbalism'), (186, 'Mining'), (393, 'Skinning')], default=0)),
                ('altProfessionExpiryDate', models.DateTimeField()),
            ],
            options={
                'db_table': 'ft_profile_altprofession',
            },
        ),
        migrations.AddField(
            model_name='profilealt',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.profilefazztoolsuser'),
        ),
        migrations.CreateModel(
            name='DataRecipeReagent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField()),
                ('reagent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.datareagent')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofessionrecipe')),
            ],
            options={
                'db_table': 'ft_data_recipereagent',
            },
        ),
        migrations.AddField(
            model_name='dataprofessionrecipe',
            name='tier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofessiontier'),
        ),
        migrations.CreateModel(
            name='DataEquipmentVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant', models.CharField(max_length=32)),
                ('stamina', models.PositiveSmallIntegerField()),
                ('armour', models.PositiveSmallIntegerField()),
                ('strength', models.PositiveSmallIntegerField()),
                ('agility', models.PositiveSmallIntegerField()),
                ('intellect', models.PositiveSmallIntegerField()),
                ('haste', models.PositiveSmallIntegerField()),
                ('mastery', models.PositiveSmallIntegerField()),
                ('vers', models.PositiveSmallIntegerField()),
                ('crit', models.PositiveSmallIntegerField()),
                ('level', models.PositiveSmallIntegerField()),
                ('quality', models.CharField(max_length=20)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataequipment')),
            ],
            options={
                'db_table': 'ft_data_equipmentvariant',
            },
        ),
        migrations.CreateModel(
            name='ProfileAltProfessionData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('altProfessionDataExpiryDate', models.DateTimeField()),
                ('profession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofession')),
                ('professionRecipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofessionrecipe')),
                ('professionTier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.dataprofessiontier')),
                ('alt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apicore.profilealtprofession')),
            ],
            options={
                'db_table': 'ft_profile_altprofessiondata',
            },
        ),
        migrations.AddConstraint(
            model_name='profilealt',
            constraint=models.UniqueConstraint(fields=('altName', 'altRealmSlug'), name='unique_alt'),
        ),
        migrations.AddConstraint(
            model_name='dataequipmentvariant',
            constraint=models.UniqueConstraint(fields=('equipment', 'variant'), name='unique_equipmentvariant'),
        ),
        migrations.AddConstraint(
            model_name='profilealtprofessiondata',
            constraint=models.UniqueConstraint(fields=('alt', 'profession', 'professionTier', 'professionRecipe'), name='unique_altprofessiondata'),
        ),
    ]
