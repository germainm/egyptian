from django.conf import settings
from django.core import management

from .literals import COMMAND_NAME_SETTINGS_SAVE


def initializer_settings_save():
    if not settings.COMMON_DISABLE_LOCAL_STORAGE:
        management.call_command(command_name=COMMAND_NAME_SETTINGS_SAVE)
