from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_medicion_co'),
    ]

    operations = [
        migrations.RenameField(
            model_name='medicion',
            old_name='CO',
            new_name='co',
        ),
    ]