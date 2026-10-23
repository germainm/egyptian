import errno
import os
import sys

import yaml

from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_str

from mayan.apps.common.serialization import yaml_dump, yaml_load
from mayan.apps.templating.template_backends import Template
from mayan.literals import ENVIRONMENT_VARIABLE_PREFIX

from .literals import (
    CONFIGURATION_FILENAME, CONFIGURATION_FILENAME_LAST_GOOD,
    DEFAULT_AUTH_PASSWORD_VALIDATORS, DEFAULT_AUTHENTICATION_BACKENDS,
    DEFAULT_SECURE_PROXY_SSL_HEADER, DEFAULT_USE_X_FORWARDED_HOST,
    DEFAULT_USE_X_FORWARDED_PORT
)
from .setting_validators import (
    check_setting_is_list_of_mappings, check_setting_is_list_of_strings,
    check_setting_secure_proxy_ssl_header
)

environment_variable_prefix = ENVIRONMENT_VARIABLE_PREFIX


def get_environment_variable_full_name(name):
    full_name = '{}{}'.format(environment_variable_prefix, name)
    return full_name


def serialize_data_to_display(data):
    result = yaml_dump(
        allow_unicode=True, data=data, default_flow_style=False
    )
    if force_str(s=result).endswith('...\n'):
        result = result[:-4]

    return result


class SettingNamespaceSingleton:
    _setting_kwargs = {}
    _setting_overrides = {}
    _settings = {}

    class SettingNotFound(Exception):
        pass

    @classmethod
    def load_config_file(cls, filepath):
        try:
            with open(file=filepath) as file_object:
                file_object.seek(0, os.SEEK_END)
                if file_object.tell():
                    file_object.seek(0)
                    try:
                        return yaml_load(stream=file_object)
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

    @classmethod
    def register_setting(cls, name, klass, kwargs=None):
        cls._settings[name] = klass
        cls._setting_kwargs[name] = kwargs or {}

    def __init__(self, global_symbol_table):
        self.global_symbol_table = global_symbol_table
        self.settings = {}
        self._config_file_content_cache = {}

        for name, klass in self.__class__._settings.items():
            kwargs = self.__class__._setting_kwargs[name].copy()
            kwargs['name'] = name
            setting = klass(**kwargs)
            setting.namespace = self
            self.settings[name] = setting

        global environment_variable_prefix
        environment_variable_prefix = os.environ.get(
            'MAYAN_ENVIRONMENT_VARIABLE_PREFIX', ENVIRONMENT_VARIABLE_PREFIX
        )

    def get_config_file_content(self):
        filepath = self.get_setting_value(name='CONFIGURATION_FILEPATH')

        try:
            return self._config_file_content_cache[filepath]
        except KeyError:
            content = self.load_config_file(filepath=filepath) or {}
            self._config_file_content_cache[filepath] = content

            return content

    def get_setting(self, name):
        return self.settings[name]

    def get_setting_value(self, name):
        try:
            setting = self.get_setting(name=name)
        except KeyError:
            raise SettingNamespaceSingleton.SettingNotFound
        else:
            return setting.get_value()

    def get_values(self, only_critical=False):
        result = {}
        for name, setting in self.settings.items():
            if only_critical and setting.critical or not only_critical:
                try:
                    result[name] = setting.get_value()
                except SettingNamespaceSingleton.SettingNotFound:
                    """
                    Not critical, we just avoid adding it to the result
                    dictionary.
                    """
                except Exception as exception:
                    raise SystemExit(
                        'Unable to load bootstrap setting; {}'.format(
                            exception
                        )
                    )

        return result

    def update_globals(self, global_symbol_table=None, only_critical=False):
        result = self.get_values(only_critical=only_critical)

        if global_symbol_table is None:
            global_symbol_table = self.global_symbol_table

        global_symbol_table.update(result)


class BaseSetting:
    @staticmethod
    def safe_string_value_to_string(value):
        return value.encode('utf-8').decode()

    def __init__(
        self, name, critical=False, default_value=None,
        has_default=False, validation_function=None
    ):
        self.critical = critical
        self.default_value = default_value
        self.has_default = has_default
        self.name = name
        self.validation_function = validation_function

    def do_load_value_from_config_file(self):
        content = self.namespace.get_config_file_content()
        try:
            return content[self.name]
        except KeyError:
            raise SettingNamespaceSingleton.SettingNotFound

    def do_load_value_from_environment(self):
        try:
            value = os.environ[
                self.get_environment_name()
            ]
        except KeyError:
            raise SettingNamespaceSingleton.SettingNotFound
        else:
            try:
                return yaml_load(stream=value)
            except yaml.YAMLError as exception:
                raise ValueError(
                    'Error loading setting environment variable "{}", '
                    'value: "{}"; {}'.format(
                        self.name, value, exception
                    )
                )

    def do_load_value_from_global_system_table(self):
        return self.namespace.global_symbol_table[self.name]

    def _get_value(self):
        try:
            return self.do_load_value_from_environment()
        except SettingNamespaceSingleton.SettingNotFound:
            try:
                return self.do_load_value_from_config_file()
            except SettingNamespaceSingleton.SettingNotFound:
                try:
                    return self.do_load_value_from_global_system_table()
                except KeyError:
                    if self.has_default:
                        return self.get_default_value()
                    else:
                        raise SettingNamespaceSingleton.SettingNotFound

    def get_default_value(self):
        return self.default_value

    def get_environment_name(self):
        full_name = get_environment_variable_full_name(name=self.name)
        return full_name

    def get_template_environment_name(self):
        template_name = self.get_template_name()
        full_name = get_environment_variable_full_name(name=template_name)
        return full_name

    def get_template_name(self):
        return 'SETTING_TEMPLATE_{}'.format(self.name)

    def get_template_string(self):
        try:
            return self.get_template_string_from_environment()
        except KeyError:
            try:
                return self.get_template_string_from_config_file()
            except KeyError:
                return self.get_template_string_from_global_system_table()

    def get_template_string_from_config_file(self):
        content = self.namespace.get_config_file_content()
        template_name = self.get_template_name()

        return content[template_name]

    def get_template_string_from_environment(self):
        template_environment_name = self.get_template_environment_name()

        return os.environ[template_environment_name]

    def get_template_string_from_global_system_table(self):
        template_name = self.get_template_name()
        return self.namespace.global_symbol_table[template_name]

    def do_value_validate(self, value):
        if not self.validation_function:
            return value

        try:
            return self.validation_function(raw_value=value, setting=self)
        except Exception as exception:
            return self.do_value_validation_error_handle(exception=exception)

    def do_value_validation_error_handle(self, exception):
        settings_ignore_errors = self.get_settings_ignore_errors()

        if settings_ignore_errors:
            sys.stderr.write(
                'WARNING: Ignoring invalid value for setting `{}`; {} Using '
                'the default value instead.\n'.format(self.name, exception)
            )
            return self.get_default_value()
        else:
            raise ImproperlyConfigured(
                'Invalid value for setting `{}`; {}'.format(
                    self.name, exception
                )
            )

    def get_settings_ignore_errors(self):
        try:
            return self.namespace.get_setting_value(
                name='SETTINGS_IGNORE_ERRORS'
            )
        except SettingNamespaceSingleton.SettingNotFound:
            return True

    def get_value(self):
        value = self.get_value_resolved()

        return self.do_value_validate(value=value)

    def get_value_resolved(self):
        try:
            return self.namespace._setting_overrides[self.name]
        except KeyError:
            try:
                template_string = self.get_template_string()
            except KeyError:
                return self._get_value()
            else:
                setting_template = Template(template_string=template_string)
                context = {}
                context.update(self.namespace.global_symbol_table)
                config_file_content = self.namespace.get_config_file_content()

                context.update(config_file_content)
                context.update(os.environ)

                value = setting_template.render(context=context)
                value = BaseSetting.safe_string_value_to_string(value=value)

                return value

    def set_value(self, value):
        self.namespace._setting_overrides[self.name] = value


class FilesystemBootstrapSetting(BaseSetting):
    def __init__(self, name, critical=False, path_parts=None):
        self.critical = critical
        self.has_default = True
        self.name = name
        self.path_parts = path_parts
        self.validation_function = None

    def _get_value(self):
        try:
            return self.do_load_value_from_environment()
        except SettingNamespaceSingleton.SettingNotFound:
            if self.has_default:
                return self.get_default_value()
            else:
                raise SettingNamespaceSingleton.SettingNotFound

    def get_default_value(self):
        try:
            BASE_DIR = self.namespace._setting_overrides['MEDIA_ROOT']
        except KeyError:
            BASE_DIR = self.namespace.global_symbol_table.get(
                'MEDIA_ROOT', self.namespace.global_symbol_table['BASE_DIR']
            )

        return os.path.join(BASE_DIR, *self.path_parts)

    def get_template_string(self):
        try:
            return self.get_template_string_from_environment()
        except KeyError:
            return self.get_template_string_from_global_system_table()


class MediaBootstrapSetting(FilesystemBootstrapSetting):
    def get_default_value(self):
        media_root = self.namespace.get_setting_value(name='MEDIA_ROOT')

        return os.path.join(media_root, *self.path_parts)


def smart_yaml_load(value):
    if isinstance(value, dict):
        return value
    else:
        stream = value or '{}'
        return yaml_load(stream=stream)



SettingNamespaceSingleton.register_setting(
    klass=MediaBootstrapSetting, kwargs={
        'critical': True, 'path_parts': (CONFIGURATION_FILENAME,)
    }, name='CONFIGURATION_FILEPATH'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'critical': True, 'has_default': True, 'default_value': False
    }, name='CONFIGURATION_FILE_IGNORE'
)


SettingNamespaceSingleton.register_setting(
    klass=MediaBootstrapSetting, kwargs={
        'critical': True, 'path_parts': (CONFIGURATION_FILENAME_LAST_GOOD,)
    }, name='CONFIGURATION_LAST_GOOD_FILEPATH'
)
SettingNamespaceSingleton.register_setting(
    klass=FilesystemBootstrapSetting, kwargs={
        'critical': True, 'path_parts': ('media',)
    }, name='MEDIA_ROOT'
)


SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True,
        'default_value': ['127.0.0.1', 'localhost', '[::1]'],
        'validation_function': check_setting_is_list_of_strings
    }, name='ALLOWED_HOSTS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='APPEND_SLASH'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True,
        'default_value': DEFAULT_AUTH_PASSWORD_VALIDATORS,
        'validation_function': check_setting_is_list_of_mappings
    }, name='AUTH_PASSWORD_VALIDATORS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True,
        'default_value': DEFAULT_AUTHENTICATION_BACKENDS,
        'validation_function': check_setting_is_list_of_strings
    }, name='AUTHENTICATION_BACKENDS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
            }
        }
    }, name='CACHES'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting,
    kwargs={
        'has_default': True,
        'default_value': False
    }, name='CSRF_COOKIE_SECURE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting,
    kwargs={
        'has_default': True,
        'default_value': [],
        'validation_function': check_setting_is_list_of_strings
    }, name='CSRF_TRUSTED_ORIGINS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting,
    kwargs={
        'has_default': True,
        'default_value': False
    }, name='CSRF_USE_SESSIONS'
)
SettingNamespaceSingleton.register_setting(
    name='DATA_UPLOAD_MAX_MEMORY_SIZE', klass=BaseSetting,
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASES'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': False
    }, name='DEBUG'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='DEFAULT_FROM_EMAIL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='DISALLOWED_USER_AGENTS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_BACKEND'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_HOST'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_HOST_PASSWORD'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_HOST_USER'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_PORT'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_TIMEOUT'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_USE_SSL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='EMAIL_USE_TLS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='FILE_UPLOAD_MAX_MEMORY_SIZE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': ['127.0.0.1'],
        'validation_function': check_setting_is_list_of_strings
    }, name='INTERNAL_IPS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': 'common:home'
    }, name='LOGIN_REDIRECT_URL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': 'authentication:login_view'
    }, name='LOGIN_URL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': 'authentication:login_view'
    }, name='LOGOUT_REDIRECT_URL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='LANGUAGES'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='LANGUAGE_CODE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='SERVER_EMAIL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True,
        'default_value': DEFAULT_SECURE_PROXY_SSL_HEADER,
        'validation_function': check_setting_secure_proxy_ssl_header
    }, name='SECURE_PROXY_SSL_HEADER'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='SESSION_COOKIE_NAME'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='SESSION_ENGINE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='STATIC_URL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='STORAGES',
    kwargs={
        'has_default': True, 'default_value': {}
    }
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='TIME_ZONE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': DEFAULT_USE_X_FORWARDED_HOST
    }, name='USE_X_FORWARDED_HOST'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': DEFAULT_USE_X_FORWARDED_PORT
    }, name='USE_X_FORWARDED_PORT'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='WSGI_APPLICATION'
)


SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': True
    }, name='CELERY_TASK_ALWAYS_EAGER'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='CELERY_BROKER_LOGIN_METHOD'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': 'memory://'
    }, name='CELERY_BROKER_URL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='CELERY_BROKER_USE_SSL'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, name='CELERY_RESULT_BACKEND'
)


SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': False
    }, name='COMMON_DISABLE_LOCAL_STORAGE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'critical': True, 'has_default': True, 'default_value': ()
    }, name='COMMON_DISABLED_APPS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'critical': True, 'has_default': True, 'default_value': ()
    }, name='COMMON_EXTRA_APPS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'critical': True, 'has_default': True, 'default_value': ()
    }, name='COMMON_EXTRA_APPS_PRE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_ENGINE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_NAME'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_USER'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_PASSWORD'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_HOST'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': None
    }, name='DATABASE_PORT'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': 0
    }, name='DATABASE_CONN_MAX_AGE'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': False
    }, name='TESTING'
)


SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': True
    }, name='SETTINGS_IGNORE_ERRORS'
)
SettingNamespaceSingleton.register_setting(
    klass=BaseSetting, kwargs={
        'has_default': True, 'default_value': True
    }, name='SETTINGS_BACKUP_ENABLED'
)
