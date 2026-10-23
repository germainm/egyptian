import django.utils.timezone

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('file_caching', '0014_alter_cache_maximum_size_old')
    ]

    operations = [
        migrations.AddField(
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now,
                help_text='Last date and time this cache partition file was '
                'read. Used to evict the least recently used files first.',
                verbose_name='Accessed'
            ), model_name='cachepartitionfile', name='accessed'
        )
    ]
