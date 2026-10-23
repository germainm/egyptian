from django.core import management

from .literals import COMMAND_NAME_AUTOADMIN_CREATE


def initializer_autoadmin_create():
    management.call_command(command_name=COMMAND_NAME_AUTOADMIN_CREATE)
