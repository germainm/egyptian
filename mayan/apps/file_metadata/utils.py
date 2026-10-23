from django.apps import apps


def get_stored_driver_id_list(document_type, driver_class_list):
    DocumentTypeDriverConfiguration = apps.get_model(
        app_label='file_metadata',
        model_name='DocumentTypeDriverConfiguration'
    )

    stored_driver_id_list = [
        driver_class.model_instance.pk for driver_class in driver_class_list
    ]

    queryset = DocumentTypeDriverConfiguration.objects.filter(
        document_type=document_type, enabled=True,
        stored_driver_id__in=stored_driver_id_list
    )

    return list(
        queryset.values_list('stored_driver_id', flat=True)
    )
