from mayan.apps.file_caching.utils import update_cache_maximum_size

from .literals import STORAGE_NAME_ASSETS_CACHE


def callback_update_asset_cache_size(setting):
    update_cache_maximum_size(
        defined_storage_name=STORAGE_NAME_ASSETS_CACHE,
        maximum_size=setting.value
    )
