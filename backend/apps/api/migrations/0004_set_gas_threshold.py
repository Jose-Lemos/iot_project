from django.db import migrations, models


def set_default_gas_threshold(apps, schema_editor):
    UmbralConfig = apps.get_model("api", "UmbralConfig")
    UmbralConfig.objects.filter(pk=1).update(gas_max=200.0)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_rename_medicion_co"),
    ]

    operations = [
        migrations.AlterField(
            model_name="umbralconfig",
            name="gas_max",
            field=models.FloatField(default=200.0),
        ),
        migrations.RunPython(
            set_default_gas_threshold,
            migrations.RunPython.noop,
        ),
    ]
