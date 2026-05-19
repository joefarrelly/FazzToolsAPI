from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apicore", "0005_datapet_alter_dataequipment_equipmenticon_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profilealt",
            name="altRace",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
