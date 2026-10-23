from pathlib import Path

from django.conf import settings
from django.core import management
from django.core.management.utils import get_random_secret_key

from mayan.apps.app_manager.exceptions import (
    InitializationStepPreconditionError
)
from mayan.literals import (
    DEFAULT_SECRET_KEY, DEFAULT_USER_SETTINGS_FOLDER, SECRET_KEY_FILENAME,
    SYSTEM_DIR, UPLOAD_TEMPORARY_DIR
)

from .literals import COMMAND_NAME_MIGRATE


def initializer_create_media_storage(force=False, **kwargs):
    if settings.COMMON_DISABLE_LOCAL_STORAGE:
        return

    path_media_root = Path(settings.MEDIA_ROOT)
    path_system = path_media_root / SYSTEM_DIR
    path_secret_key = path_system / SECRET_KEY_FILENAME

    try:
        path_media_root.mkdir()
    except FileExistsError as exception:
        if not force:
            raise InitializationStepPreconditionError(
                'Existing media files. Backup, remove this folder, and try '
                'again. Or use the --force argument.'
            ) from exception

    (path_media_root / '__init__.py').touch()

    initializer_create_user_settings_folder()

    initializer_create_upload_temporary_folder()

    try:
        path_system.mkdir()
    except FileExistsError as exception:
        if not force:
            raise InitializationStepPreconditionError(
                'System folder already exists.'
            ) from exception

    with path_secret_key.open(mode='w') as file_object:
        secret_key = get_random_secret_key()
        file_object.write(secret_key)

    settings.SECRET_KEY = secret_key


def initializer_create_user_settings_folder(**kwargs):
    if not settings.COMMON_DISABLE_LOCAL_STORAGE:
        path_user_settings = Path(
            settings.MEDIA_ROOT
        ) / DEFAULT_USER_SETTINGS_FOLDER

        path_user_settings.mkdir(exist_ok=True)

        (path_user_settings / '__init__.py').touch()


def initializer_create_upload_temporary_folder(**kwargs):
    if not settings.COMMON_DISABLE_LOCAL_STORAGE:
        path_upload_temporary = Path(
            settings.MEDIA_ROOT
        ) / UPLOAD_TEMPORARY_DIR

        path_upload_temporary.mkdir(exist_ok=True)


def initializer_initial_setup_migrate(**kwargs):
    management.call_command(
        command_name=COMMAND_NAME_MIGRATE, interactive=False
    )


def initializer_upgrade_migrate(**kwargs):
    management.call_command(
        command_name=COMMAND_NAME_MIGRATE, fake_initial=True,
        interactive=False
    )


def initializer_verify_secret_key(**kwargs):
    if settings.SECRET_KEY == DEFAULT_SECRET_KEY:
        raise InitializationStepPreconditionError(
            'SECRET_KEY value not set. If local storage is disabled, pass '
            'the SECRET_KEY via an environment variable. A SECRET_KEY value '
            'can be generated using the `common_generate_random_secret_key` '
            'command.'
        )
