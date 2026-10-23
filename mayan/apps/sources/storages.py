from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.storage.classes import DefinedStorage

from .literals import STORAGE_NAME_SOURCE_CACHE_FOLDER
from .settings import (
    setting_source_cache_storage_backend,
    setting_source_cache_storage_backend_arguments
)

storage_source_cache = DefinedStorage(
    dotted_path=setting_source_cache_storage_backend.value,
    error_message=format_lazy(
        _(
            message='Unable to initialize the staging folder file image '
            'storage. Check the settings {} and {} for formatting '
            'errors.'
        ), setting_source_cache_storage_backend.global_name,
        setting_source_cache_storage_backend_arguments.global_name
    ), kwargs=setting_source_cache_storage_backend_arguments.value,
    label=_(message='Sources cache'), name=STORAGE_NAME_SOURCE_CACHE_FOLDER
)
