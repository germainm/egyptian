import logging

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from .exceptions import SettingsException
from .setting_data_types import DATA_TYPE_FUNCTION_MAP
from .utils import serialize_data_to_display

logger = logging.getLogger(name=__name__)


class SettingMetaclass(type):
    _registry = {}

    def __call__(mcls, namespace, global_name, **kwargs):
        if global_name in mcls._registry:
            raise ImproperlyConfigured(
                'Setting `{}` already exists.'.format(global_name)
            )
        else:
            instance = super().__call__(
                namespace=namespace, global_name=global_name, **kwargs
            )
            mcls._registry[global_name] = instance

        return instance

    @classmethod
    def unregister(mcls, instance):
        mcls._registry.pop(instance.global_name, None)


class SettingMixinDoers:
    def do_cache_invalidate(self):
        self.value_loaded = False

        cluster = self.get_cluster()
        cluster.do_template_cache_invalidate()

    def do_namespace_join(self):
        self.namespace.do_setting_join(setting=self)

    def do_post_edit_function_call(self):
        if self.post_edit_function:
            try:
                self.post_edit_function(setting=self)
            except Exception as exception:
                message = (
                    'Unable to execute setting post update function '
                    'for setting "{}". Verify the value of the setting or '
                    'rollback to the previous known working configuration '
                    'file; {}'.format(self.global_name, exception)
                )
                raise SettingsException(message) from exception

    def do_ready(self):
        self.do_value_cache()
        self.do_post_edit_function_call()

    def do_value_cache(self):
        self.value

    def do_value_load(self):
        logger.debug('%s %s', '=' * 40, self.global_name)
        cluster = self.get_cluster()

        try:
            value, self.domain_dict = cluster.get_domains_value(
                key=self.global_name
            )
        except KeyError:
            value = self.default

        logger.debug('cluster read value value: %s', value)

        value_validated = self.do_value_validate(value=value)

        logger.debug('value_validated: %s', value_validated)

        logger.debug('self.value_error: %s', self.value_error)

        if self.value_error:
            value_original = self.default
        else:
            value_original = value_validated

        value_expressed = Setting.express_promises(value=value_original)

        self.do_value_set(value=value_expressed)

        self.value_loaded = True

        logger.debug('Final value: %s', self._value)

    def do_value_pending_set(self, value):
        value = self.do_value_validate(value=value)

        if self.value_error is None:
            value_expressed = Setting.express_promises(value=value)
            cluster = self.get_cluster()
            cluster.do_setting_value_pending_set(
                setting=self, value=value_expressed
            )

    def do_value_override(self, value):
        value_validated = self.do_value_validate(value=value)

        if self.value_error is None:
            self.value_loaded = True
            value_expressed = Setting.express_promises(value=value_validated)
            self.do_value_set(value=value_expressed)

    def do_value_set(self, value):
        value_previous = self._value

        self._value = value

        if value != value_previous:
            cluster = self.get_cluster()
            cluster.do_template_cache_invalidate()

    def do_value_validate(self, value):
        self.value_error = None

        if self.data_type is not None:
            data_type_function = self.get_data_type_function()

            try:
                value = data_type_function(value)
            except Exception as exception:
                self.value_error = str(exception)

        try:
            value = self.do_value_raw_validate(raw_value=value)
        except Exception as exception:
            self.value_error = str(exception)
        else:
            return value

    def do_value_raw_validate(self, raw_value):
        if self.validation_function:
            try:
                result = self.validation_function(
                    raw_value=raw_value, setting=self
                )
            except Exception as exception:
                raise ValidationError(
                    _(
                        message='Error validating value `%(value)s` for '
                        'setting `%(global_name)s`; %(exception)s'
                    ) % {
                        'value': raw_value, 'global_name': self.global_name,
                        'exception': exception
                    }
                ) from exception
            else:
                return result
        else:
            return raw_value

    def do_value_revert(self):
        self.pending_value_set = False
        cluster = self.get_cluster()
        cluster.do_setting_revert(setting=self)


class SettingMixinGetters:
    def get_cluster(self):
        return self.namespace.cluster

    def get_data_type_function(self):
        return DATA_TYPE_FUNCTION_MAP.get(self.data_type, self.data_type)

    def get_display_value(self):
        value = self.get_value_pending()
        result = serialize_data_to_display(data=value)
        return result

    def get_display_default_value(self):
        return serialize_data_to_display(data=self.default)

    get_display_default_value.short_description = _(message='Default value')
    get_display_default_value.help_text = _(
        message='The value the setting reverts to when nothing overrides it.'
    )

    def get_load_error_text(self):
        error_list = []

        if self.value_error is not None:
            error_list.append(
                force_str(s=self.value_error)
            )

        for domain_name, domain_value in self.domain_dict.items():
            try:
                domain_error = domain_value['error']
            except KeyError:
                """The domain reported no error."""
            else:
                error_list.append(
                    force_str(s=domain_error)
                )

        return '\n'.join(error_list)

    get_load_error_text.short_description = _(message='Error')

    def get_has_load_error(self):
        if self.value_error is not None:
            return True
        else:
            for domain_name, value in self.domain_dict.items():
                if 'error' in value:
                    return True

        return False

    get_has_load_error.short_description = _(message='Has errors')
    get_has_load_error.help_text = _(
        message='Indicates that this setting was not loaded correctly. '
        'Settings with errors revert to their default value.'
    )

    def get_has_value_new(self):
        value_pending = self.get_value_pending()
        return value_pending != self.value

    get_has_value_new.short_description = _(message='Modified')
    get_has_value_new.help_text = _(
        message='The value of this setting has been modified since the last '
        'restart.'
    )

    def get_has_value_pending(self):
        cluster = self.get_cluster()
        try:
            value_pending = cluster.get_setting_value_pending(setting=self)
        except KeyError:
            return False
        else:
            return value_pending != self._value

    def get_is_overridden(self):
        return self.value != self.default

    get_is_overridden.short_description = _(message='Overridden')
    get_is_overridden.help_text = _(
        message='The value of the setting is being overridden from its '
        'default. If the source of the change is an environment '
        'variable, changing its value via the user interface will not have '
        'any effect.'
    )

    def get_value_choices(self):
        if callable(self.choices):
            return self.choices()
        else:
            return self.choices

    get_value_choices.short_description = _(message='Choices')
    get_value_choices.help_text = _(
        message='Possible values allowed for this setting.'
    )

    def get_value_pending(self, value_pending_map=None):
        if value_pending_map is None:
            cluster = self.get_cluster()

            try:
                value_pending = cluster.get_setting_value_pending(
                    setting=self
                )
            except KeyError:
                return self.value
            else:
                return value_pending

        try:
            value_pending = value_pending_map[self.global_name]
        except KeyError:
            return self.value
        else:
            return value_pending


class Setting(
    SettingMixinDoers, SettingMixinGetters, metaclass=SettingMetaclass
):
    @staticmethod
    def express_promises(value):
        if isinstance(value, (list, tuple)):
            return [
                Setting.express_promises(item) for item in value
            ]
        elif isinstance(value, Promise):
            return force_str(s=value)
        else:
            return value

    def __init__(
        self, global_name, default, namespace, choices=None,
        data_type=None, help_text=None, is_path=False,
        post_edit_function=None, validation_function=None
    ):
        self.choices = choices
        self.data_type = data_type
        self.default = default
        self.domain_dict = {}
        self.environment_variable = False
        self.global_name = global_name
        self.help_text = help_text
        self.namespace = namespace
        self.post_edit_function = post_edit_function
        self.validation_function = validation_function
        self.value_error = None
        self._value = None
        self.value_loaded = False

        self.do_namespace_join()

    def __repr__(self):
        cluster = self.get_cluster()
        return 'Setting: {}-{}-{}: {}'.format(
            cluster, self.namespace, self.global_name, self.value
        )

    def __str__(self):
        return str(self.global_name)

    @property
    def pk(self):
        return self.global_name

    @property
    def value(self):
        if not self.value_loaded:
            self.do_value_load()

        return self._value
