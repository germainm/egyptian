from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.storage.classes import DefinedStorage

from .literals import STORAGE_NAME_SIGNATURE_CAPTURES_CACHE
from .settings import (
    setting_signature_capture_cache_storage_backend,
    setting_signature_capture_cache_storage_backend_arguments
)

storage_signature_captures_cache = DefinedStorage(
    dotted_path=setting_signature_capture_cache_storage_backend.value,
    error_message=format_lazy(
        _(
            message='Unable to initialize the converter signature capture cache'
            'storage. Check the settings {} and {} for formatting '
            'errors.'
        ), setting_signature_capture_cache_storage_backend.global_name,
        setting_signature_capture_cache_storage_backend_arguments.global_name
    ), label=_(message='Signature captures cache'),
    name=STORAGE_NAME_SIGNATURE_CAPTURES_CACHE,
    kwargs=setting_signature_capture_cache_storage_backend_arguments.value
)
