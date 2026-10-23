from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.storage.classes import DefinedStorage

from .literals import STORAGE_NAME_WORKFLOW_CACHE
from .settings import (
    setting_workflow_image_cache_storage_backend,
    setting_workflow_image_cache_storage_backend_arguments
)

storage_workflow_image = DefinedStorage(
    dotted_path=setting_workflow_image_cache_storage_backend.value,
    error_message=format_lazy(
        _(
            message='Unable to initialize the workflow preview '
            'storage. Check the settings {} and {} for formatting '
            'errors.'
        ), setting_workflow_image_cache_storage_backend.global_name,
        setting_workflow_image_cache_storage_backend_arguments.global_name
    ),
    label=_(message='Workflow preview images'),
    name=STORAGE_NAME_WORKFLOW_CACHE,
    kwargs=setting_workflow_image_cache_storage_backend_arguments.value
)
