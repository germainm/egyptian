from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('file_metadata', '0019_alter_filemetadataentry_options')
    ]

    operations = [
        migrations.AlterField(
            model_name='filemetadataentry',
            field=models.TextField(
                blank=True,
                help_text='Value of the file metadata entry.',
                verbose_name='Value'
            ),
            name='value'
        )
    ]
