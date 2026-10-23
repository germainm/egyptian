from django.db import migrations


def code_inactive_document_version_active_clear(apps, schema_editor):
    Document = apps.get_model(app_label='documents', model_name='Document')

    alias = schema_editor.connection.alias

    queryset = Document.objects.using(alias=alias).filter(
        version_active__active=False
    )

    queryset.update(version_active=None)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0096_restore_document_file_timestamp_index')
    ]

    operations = [
        migrations.RunPython(
            code=code_inactive_document_version_active_clear,
            elidable=True, reverse_code=migrations.RunPython.noop
        )
    ]
