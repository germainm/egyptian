from django.conf import settings
from django.core import management

from .literals import COMMAND_NAME_DEPENDENCIES_INSTALL


def initializer_dependencies_install(no_dependencies=False, **kwargs):
    if no_dependencies or settings.COMMON_DISABLE_LOCAL_STORAGE:
        return

    management.call_command(command_name=COMMAND_NAME_DEPENDENCIES_INSTALL)
