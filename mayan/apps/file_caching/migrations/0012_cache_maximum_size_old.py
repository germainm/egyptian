from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('file_caching', '0011_alter_cache_maximum_size')
    ]

    operations = [
        migrations.AddField(
            field=models.PositiveBigIntegerField(
                editable=False,
                help_text='Previous maximum size of the cache in bytes.',
                null=True, verbose_name='Old maximum size'
            ), model_name='cache', name='maximum_size_old'
        )
    ]
