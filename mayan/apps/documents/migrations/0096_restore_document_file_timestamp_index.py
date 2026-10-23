from django.db import migrations


def code_document_file_timestamp_index_create(apps, schema_editor):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    field = DocumentFile._meta.get_field(field_name='timestamp')

    existing_index_names = schema_editor._constraint_names(
        column_names=[field.column], index=True, model=DocumentFile
    )

    if not existing_index_names:
        statement = schema_editor._create_index_sql(
            fields=[field], model=DocumentFile
        )
        schema_editor.execute(sql=statement)


def code_document_file_timestamp_index_delete(apps, schema_editor):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    field = DocumentFile._meta.get_field(field_name='timestamp')

    existing_index_names = schema_editor._constraint_names(
        column_names=[field.column], index=True, model=DocumentFile
    )

    for index_name in existing_index_names:
        statement = schema_editor._delete_index_sql(
            model=DocumentFile, name=index_name
        )
        schema_editor.execute(sql=statement)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0095_restore_document_file_document_index')
    ]

    operations = [
        migrations.RunPython(
            code=code_document_file_timestamp_index_create,
            reverse_code=code_document_file_timestamp_index_delete
        )
    ]
