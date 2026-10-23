from django.db import migrations

from mayan.apps.databases.literals import (
    DJANGO_POSITIVE_INTEGER_FIELD_MAX_VALUE
)


def code_document_file_size_update(apps, schema_editor):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    queryset = DocumentFile.objects.filter(
        size=DJANGO_POSITIVE_INTEGER_FIELD_MAX_VALUE
    )

    for document_file in queryset:
        name = document_file.file.name
        document_file.file.close()

        if document_file.file.storage.exists(name=name):
            document_file.size = document_file.file.storage.size(name=name)
            document_file.save(
                update_fields=('size',)
            )


def reverse_code_document_file_size_update(apps, schema_editor):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    queryset = DocumentFile.objects.filter(
        size__gt=DJANGO_POSITIVE_INTEGER_FIELD_MAX_VALUE
    )

    for document_file in queryset:
        name = document_file.file.name
        document_file.file.close()

        if document_file.file.storage.exists(name=name):
            document_file.size = DJANGO_POSITIVE_INTEGER_FIELD_MAX_VALUE
            document_file.save(
                update_fields=('size',)
            )


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0081_alter_documentfile_size')
    ]

    operations = [
        migrations.RunPython(
            code=code_document_file_size_update,
            reverse_code=reverse_code_document_file_size_update
        )
    ]
