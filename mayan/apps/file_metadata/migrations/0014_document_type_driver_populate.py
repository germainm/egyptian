from django.db import migrations


def code_document_type_driver_configuration_populate(apps, schema_editor):
    DocumentType = apps.get_model(
        app_label='documents', model_name='DocumentType'
    )
    DocumentTypeDriverConfiguration = apps.get_model(
        app_label='file_metadata', model_name='DocumentTypeDriverConfiguration'
    )
    DocumentTypeSettings = apps.get_model(
        app_label='file_metadata', model_name='DocumentTypeSettings'
    )
    StoredDriver = apps.get_model(
        app_label='file_metadata', model_name='StoredDriver'
    )

    for document_type in DocumentType.objects.using(alias=schema_editor.connection.alias).all():
        try:
            document_type_file_metadata_settings = DocumentTypeSettings.objects.get(document_type=document_type)
        except DocumentTypeSettings.DoesNotExist:
            enabled = True
        else:
            enabled = document_type_file_metadata_settings.auto_process

        for stored_driver in StoredDriver.objects.using(alias=schema_editor.connection.alias).all():
            DocumentTypeDriverConfiguration.objects.update_or_create(
                defaults={'enabled': enabled}, document_type=document_type,
                stored_driver=stored_driver
            )


class Migration(migrations.Migration):
    dependencies = [
        ('file_metadata', '0013_documenttypedriverconfiguration')
    ]

    operations = [
        migrations.RunPython(
            code=code_document_type_driver_configuration_populate,
            reverse_code=migrations.RunPython.noop
        )
    ]
