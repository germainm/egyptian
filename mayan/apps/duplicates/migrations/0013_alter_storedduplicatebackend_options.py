from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('duplicates', '0012_alter_duplicatebackendentry_options')
    ]

    operations = [
        migrations.AlterModelOptions(
            name='storedduplicatebackend',
            options={
                'ordering': ('backend_path',),
                'verbose_name': 'Stored duplicate backend',
                'verbose_name_plural': 'Stored duplicate backends'
            }
        )
    ]
