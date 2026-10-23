from mayan.apps.file_caching.utils import update_cache_maximum_size

from .literals import STORAGE_NAME_SIGNATURE_CAPTURES_CACHE


def callback_update_signature_capture_cache_size(setting):
    update_cache_maximum_size(
        defined_storage_name=STORAGE_NAME_SIGNATURE_CAPTURES_CACHE,
        maximum_size=setting.value
    )
