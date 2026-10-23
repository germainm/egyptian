from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('duplicates', '0011_alter_duplicatebackendentry_document')
    ]

    operations = [
        migrations.AlterModelOptions(
            name='duplicatebackendentry', options={
                'ordering': ('stored_backend__backend_path',),
                'verbose_name': 'Duplicated backend entry',
                'verbose_name_plural': 'Duplicated backend entries'
            }
        )
    ]
