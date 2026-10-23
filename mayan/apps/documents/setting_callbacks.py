from mayan.apps.file_caching.utils import update_cache_maximum_size

from .literals import (
    STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE,
    STORAGE_NAME_DOCUMENT_VERSION_PAGE_IMAGE_CACHE
)


def callback_update_document_file_page_image_cache_size(setting):
    update_cache_maximum_size(
        defined_storage_name=STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE,
        maximum_size=setting.value
    )


def callback_update_document_version_page_image_cache_size(setting):
    update_cache_maximum_size(
        defined_storage_name=STORAGE_NAME_DOCUMENT_VERSION_PAGE_IMAGE_CACHE,
        maximum_size=setting.value
    )
