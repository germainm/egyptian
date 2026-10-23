from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('file_caching', '0013_auto_20260523_0650')
    ]

    operations = [
        migrations.AlterField(
            field=models.PositiveBigIntegerField(
                editable=False,
                help_text='Previous maximum size of the cache in bytes.',
                verbose_name='Old maximum size'
            ), model_name='cache', name='maximum_size_old'
        )
    ]
