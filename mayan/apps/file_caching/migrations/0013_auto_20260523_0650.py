from django.db import migrations
from django.db.models import F


def backfill_old_max_size(apps, schema_editor):
    Cache = apps.get_model('file_caching', 'Cache')

    Cache.objects.filter(maximum_size_old__isnull=True).update(
        maximum_size_old=F('maximum_size')
    )


class Migration(migrations.Migration):
    dependencies = [
        ('file_caching', '0012_cache_maximum_size_old')
    ]

    operations = [
        migrations.RunPython(
            code=backfill_old_max_size, reverse_code=migrations.RunPython.noop
        )
    ]
