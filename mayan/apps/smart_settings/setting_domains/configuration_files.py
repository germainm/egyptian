import datetime
import errno
import functools
import logging
import os
from pathlib import Path
from shutil import copyfile
import sys
import tempfile

import yaml

from django.conf import settings

import mayan
from mayan.apps.common.serialization import yaml_dump, yaml_load

from ..domains import SettingDomain
from ..exceptions import SettingsDomainError
from ..literals import COMMAND_NAME_SETTINGS_REVERT

logger = logging.getLogger(name=__name__)


class SettingDomainConfigurationFile(SettingDomain):
    name = 'config_file'

    @staticmethod
    def deserialize_stream(stream):
        return yaml_load(stream=stream)

    @staticmethod
    def serialize_data(data):
        result = yaml_dump(data=data, default_flow_style=False)
        return result


    @classmethod
    def _do_configuration_file_read(cls, filepath):
        try:
            with open(file=filepath) as file_object:
                file_object.seek(0, os.SEEK_END)
                if file_object.tell():
                    file_object.seek(0)
                    try:
                        return cls.deserialize_stream(stream=file_object)
                    except yaml.YAMLError as exception:
                        raise SystemExit(
                            'Error loading configuration file: {}; {}'.format(
                                filepath, exception
                            )
                        )
        except IOError as exception:
            if exception.errno == errno.ENOENT:
                return {}
            else:
                raise

    @staticmethod
    def _do_configuration_file_write(filepath, data):
        path = Path(filepath)

        directory = path.parent

        try:
            mode = path.stat().st_mode & 0o777
        except OSError:
            mode = None

        file_descriptor, temporary_filepath = tempfile.mkstemp(
            dir=directory, prefix='.config_', suffix='.tmp'
        )
        temporary_path = Path(temporary_filepath)

        try:
            with os.fdopen(file_descriptor, mode='w') as file_object:
                file_object.write(data)
                file_object.flush()
                os.fsync(file_object.fileno())

            if mode is not None:
                temporary_path.chmod(mode=mode)

            temporary_path.replace(target=path)
        except BaseException:
            try:
                temporary_path.unlink()
            except OSError:
                """The temporary file was already renamed or removed."""

            raise

    @classmethod
    def _do_last_known_good_save(cls, data):
        if COMMAND_NAME_SETTINGS_REVERT not in sys.argv and not settings.CONFIGURATION_FILE_IGNORE:
            kwargs = {'filepath': settings.CONFIGURATION_LAST_GOOD_FILEPATH}

            cls.do_make_persistent(data=data, kwargs=kwargs)

    @classmethod
    @functools.cache
    def _get_configuration_file_content(cls):
        if settings.CONFIGURATION_FILE_IGNORE:
            return {}
        else:
            data = cls._do_configuration_file_read(
                filepath=settings.CONFIGURATION_FILEPATH
            ) or {}

            return data



    @classmethod
    def do_cache_invalidate(cls):
        cls._get_configuration_file_content.cache_clear()

    @classmethod
    def do_make_persistent(cls, data, kwargs=None):
        kwargs = kwargs or {}
        filepath = kwargs.get('filepath', None)

        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            if not filepath:
                filepath = settings.CONFIGURATION_FILEPATH

            data_serialized = cls.serialize_data(data=data)

            line_version = '# Version: {} {}'.format(
                mayan.__version__, mayan.__build_string__
            )
            line_date = '# Date and time: {}'.format(
                datetime.datetime.now()
            )
            data_serialized = '{}\n{}\n{}'.format(
                line_version, line_date, data_serialized
            )

            try:
                cls._do_configuration_file_write(
                    data=data_serialized, filepath=filepath
                )
            except IOError as exception:
                if exception.errno == errno.ENOENT:
                    logger.warning(
                        'The path to the configuration file `%s` doesn\'t '
                        'exist. It is not possible to save the backup file.',
                        filepath
                    )
        else:
            logger.info(
                'Local storage is disabled, skip saving configuration.'
            )

    @classmethod
    def do_ready(cls, data):
        if settings.SETTINGS_BACKUP_ENABLED:
            cls._do_last_known_good_save(data=data)

    @classmethod
    def do_revert(cls):
        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            try:
                copyfile(
                    src=settings.CONFIGURATION_LAST_GOOD_FILEPATH,
                    dst=settings.CONFIGURATION_FILEPATH
                )
            except IOError as exception:
                if exception.errno == errno.ENOENT:
                    raise SettingsDomainError(
                        'There is no last valid version to restore.'
                    ) from exception
                else:
                    raise
        else:
            logger.info(
                'Local storage is disabled, cannot revert not existing '
                'configuration.'
            )


    @classmethod
    def get_key_value(cls, key):
        content = cls._get_configuration_file_content()
        value = content[key]
        return value
