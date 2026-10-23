from django.apps import apps


from .literals import STORAGE_NAME_SOURCE_CACHE_FOLDER
from .settings import setting_source_cache_maximum_size


def handler_create_source_cache(sender, **kwargs):
    Cache = apps.get_model(app_label='file_caching', model_name='Cache')

    Cache.objects.update_or_create(
        defaults={
            'maximum_size': setting_source_cache_maximum_size.value,
        }, defined_storage_name=STORAGE_NAME_SOURCE_CACHE_FOLDER
    )


def handler_delete_interval_source_periodic_task(sender, instance, **kwargs):
    Source = apps.get_model(
        app_label='sources', model_name='Source'
    )

    for source in Source.objects.all():
        backend_instance = source.get_backend_instance()

        if backend_instance.kwargs.get('document_type') == instance:
            try:
                backend_instance.delete_periodic_task()
            except AttributeError:
                """
                The source has a document type but is not a periodic source,
                """
