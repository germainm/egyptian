from mayan.apps.file_caching.utils import update_cache_maximum_size

from .literals import STORAGE_NAME_SOURCE_CACHE_FOLDER


def callback_update_source_cache_size(setting):
    update_cache_maximum_size(
        defined_storage_name=STORAGE_NAME_SOURCE_CACHE_FOLDER,
        maximum_size=setting.value
    )
