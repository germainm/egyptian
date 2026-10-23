from django.conf import settings
from django.core import management

from .literals import COMMAND_NAME_APPEARANCE_PREPARE_STATIC


def initializer_appearance_prepare_static(no_dependencies=False, **kwargs):
    if no_dependencies or settings.COMMON_DISABLE_LOCAL_STORAGE:
        return

    management.call_command(
        command_name=COMMAND_NAME_APPEARANCE_PREPARE_STATIC,
        interactive=False
    )
