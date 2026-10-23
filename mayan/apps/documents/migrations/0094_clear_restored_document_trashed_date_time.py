from django.db import migrations


def code_restored_document_trashed_date_time_clear(apps, schema_editor):
    Document = apps.get_model(app_label='documents', model_name='Document')

    alias = schema_editor.connection.alias

    queryset = Document.objects.using(alias=alias).filter(
        in_trash=False, trashed_date_time__isnull=False
    )

    queryset.update(trashed_date_time=None)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0093_remove_favorite_document_state')
    ]

    operations = [
        migrations.RunPython(
            code=code_restored_document_trashed_date_time_clear,
            elidable=True, reverse_code=migrations.RunPython.noop
        )
    ]
