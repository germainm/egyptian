from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('file_metadata', '0018_rename_internal_name')
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filemetadataentry',
            options={
                'ordering': ('internal_name', 'key'),
                'verbose_name': 'File metadata entry',
                'verbose_name_plural': 'File metadata entries'
            }
        )
    ]
