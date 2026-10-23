from django.apps import apps

from .events import event_document_created, event_document_edited
from .literals import (
    STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE,
    STORAGE_NAME_DOCUMENT_VERSION_PAGE_IMAGE_CACHE
)
from .settings import (
    setting_document_file_page_image_cache_maximum_size,
    setting_document_version_page_image_cache_maximum_size
)


def handler_create_document_file_page_image_cache(sender, **kwargs):
    Cache = apps.get_model(app_label='file_caching', model_name='Cache')
    Cache.objects.update_or_create(
        defaults={
            'maximum_size': setting_document_file_page_image_cache_maximum_size.value,
        }, defined_storage_name=STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE
    )


def handler_create_document_version_page_image_cache(sender, **kwargs):
    Cache = apps.get_model(app_label='file_caching', model_name='Cache')
    Cache.objects.update_or_create(
        defaults={
            'maximum_size': setting_document_version_page_image_cache_maximum_size.value,
        },
        defined_storage_name=STORAGE_NAME_DOCUMENT_VERSION_PAGE_IMAGE_CACHE
    )


def handler_document_event_on_save(sender, instance, created, **kwargs):
    _event_ignore = getattr(instance, '_event_ignore', False)
    if not _event_ignore:
        user = getattr(instance, '_event_actor', None)

        if created:
            action_object = getattr(
                instance, '_event_action_object', instance.document_type
            )

            event_document_created.commit(
                action_object=action_object, actor=user, target=instance
            )
        else:
            action_object = getattr(instance, '_event_action_object', None)

            event_document_edited.commit(
                action_object=action_object, actor=user, target=instance
            )
