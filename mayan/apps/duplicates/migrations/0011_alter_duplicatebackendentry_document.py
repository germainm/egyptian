from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0091_fix_documenttype_verbose_name'),
        ('duplicates', '0010_auto_20210419_0709')
    ]

    operations = [
        migrations.AlterField(
            model_name='duplicatebackendentry', name='document',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='duplicate_backend_entries',
                to='documents.document', verbose_name='Document'
            )
        )
    ]
