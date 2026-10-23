import logging

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.views.template_cache_sources import (
    TemplateCacheSourceMixin, TemplateCacheSourceRegistry
)

from .exceptions import SettingsDomainError
from .literals import SMART_SETTINGS_NAMESPACES_NAME
from .namespaces import SettingNamespace

logger = logging.getLogger(name=__name__)


class MixinSettingClusterDoers:
    def do_cache_invalidate(self):
        for namespace in self.namespace_dict.values():
            namespace.do_cache_invalidate()

        for domain in self.get_domain_list():
            domain.do_cache_invalidate()

    def do_make_persistent(self, kwargs=None):
        data = self.get_data()
        kwargs = kwargs or {}

        for domain in self.get_domain_list():
            domain.do_make_persistent(data=data, kwargs=kwargs)

    def do_namespace_add(self, **kwargs):
        setting_namespace = SettingNamespace(cluster=self, **kwargs)
        return setting_namespace

    def do_namespace_join(self, namespace):
        self.namespace_dict[namespace.name] = namespace

    def do_namespace_metadata_update(self, namespace, metadata):
        self.namespace_metadata.setdefault(
            namespace.name, {}
        )

        self.namespace_metadata[namespace.name].update(metadata)

    def do_namespace_remove(self, namespace):
        for setting in namespace.get_setting_list():
            self.setting_dict.pop(setting.global_name, None)

        self.namespace_dict.pop(namespace.name)
        SettingNamespace.unregister(instance=namespace)

    def do_ready(self):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        for namespace in self.get_namespace_list():
            namespace.do_ready()

        data = self.get_data()

        for domain in self.get_domain_list():
            domain.do_ready(data=data)

        ContentType.objects.clear_cache()

        setting_list = self.get_setting_list()
        logger.debug(
            'Settings in cluster: %d', len(setting_list)
        )

    def do_revert(self, path=None):
        for domain in self.get_domain_list():
            domain.do_revert()

    def do_setting_join(self, setting):
        self.setting_dict[setting.global_name] = setting

    def do_setting_remove(self, setting):
        for domain in self.get_domain_list():
            domain.do_key_remove(setting=setting)

        self.setting_dict.pop(setting.global_name)

    def do_setting_revert(self, setting):
        domain_list = self.get_domain_list()

        for domain in domain_list:
            domain.do_key_revert(key=setting.global_name)

    def do_setting_value_pending_set(self, setting, value):
        if value == setting.value:
            self.do_setting_revert(setting=setting)
        else:
            domain_list = self.get_domain_list()

            for domain in domain_list:
                domain.do_key_update_value_pending(
                    key=setting.global_name, value=value
                )


class MixinSettingClusterGetters:
    def get_data(self, filter_term=None, namespace_name=None):
        result = {}

        if namespace_name:
            namespace_list = (
                self.get_namespace(name=namespace_name),
            )
        else:
            namespace_list = self.get_namespace_list()
            result[SMART_SETTINGS_NAMESPACES_NAME] = self.namespace_metadata

        value_pending_map = self.get_setting_value_pending_map()

        for namespace in namespace_list:
            namespace_data = namespace.get_settings_as_data(
                filter_term=filter_term, value_pending_map=value_pending_map
            )

            result.update(namespace_data)

        return result

    def get_domain(self, name):
        for domain in self.get_domain_list():
            if domain.name == name:
                return domain

        return KeyError(
            'Unknown domain `{}`.'.format(name)
        )

    def get_domain_list(self):
        list_sorted = sorted(
            self.domain_list, key=lambda domain: domain[1]
        )

        result = [
            item[0] for item in list_sorted
        ]

        return result

    def get_domain_value(self, domain, key):
        try:
            domain_value = domain.get_key_value(key=key)
        except SettingsDomainError as exception:
            raise SettingsDomainError(
                _(
                    message='Error loading value for key '
                    '`%(key)s` from domain `%(domain_name)s`; '
                    '%(exception)s'
                ) % {
                    'domain_name': domain.name, 'exception': exception,
                    'key': key
                }
            ) from exception
        else:
            return domain_value

    def get_domains_value(self, key):
        domain_dict = {}
        domain_list = self.get_domain_list()
        found = False
        value = None

        for domain in domain_list:
            logger.debug('Domain: %s', domain.name)

            try:
                value = self.get_domain_value(
                    domain=domain, key=key
                )
            except KeyError:
                """Ignore domain and continue."""
            except SettingsDomainError as exception:
                if settings.SETTINGS_IGNORE_ERRORS:
                    logger.error(msg=exception)
                    domain_dict[domain.name] = {
                        'error': str(exception)
                    }
                else:
                    raise
            else:
                logger.debug('Domain found: %s', found)
                found = True

        if found:
            return value, domain_dict
        else:
            raise KeyError

    def get_is_changed(self):
        value_pending_map = self.get_setting_value_pending_map()

        for setting in self.get_setting_list():
            try:
                value_pending = value_pending_map[setting.global_name]
            except KeyError:
                """
                No pending value. `get_value_pending` returns the value in
                use for this case, which never differs from itself.
                """
            else:
                if value_pending != setting.value:
                    return True

        return False

    def get_setting_value_pending_map(self):
        result = {}

        for domain in self.get_domain_list():
            result.update(
                domain.get_key_value_pending_map()
            )

        return result

    def get_namespace(self, name):
        return self.namespace_dict[name]

    def get_namespace_configuration(self, name):
        namespace_configuration_map = self.get_namespace_configuration_map()

        return namespace_configuration_map.get(
            name, {}
        )

    def get_namespace_configuration_map(self):
        configuration_file_content = self.get_data()

        return configuration_file_content.get(
            SMART_SETTINGS_NAMESPACES_NAME, {}
        )

    def get_namespace_list(self):
        values = self.namespace_dict.values()
        result = sorted(values, key=lambda x: x.label)

        return result

    def get_namespace_metadata(self, namespace):
        domain_list = self.get_domain_list()
        namespace_metadata_map = {}

        for domain in domain_list:
            try:
                namespace_metadata_map = self.get_domain_value(
                    domain=domain, key=SMART_SETTINGS_NAMESPACES_NAME
                )
            except KeyError:
                """Ignore and continue."""

        return namespace_metadata_map.get(
            namespace.name, {}
        )

    def get_namespace_version_list(self, namespace):
        metadata = self.get_namespace_metadata(namespace=namespace)

        version_old = metadata.get('version')

        return (version_old, namespace.version)

    def get_setting(self, global_name):
        return self.setting_dict[global_name]

    def get_setting_list(self):
        return self.setting_dict.values()

    def get_setting_value_pending(self, setting):
        domain_list = self.get_domain_list()
        found = False
        value = None

        for domain in domain_list:
            try:
                domain_value = domain.get_key_value_pending(
                    key=setting.global_name
                )
            except KeyError:
                """Ignore and try the next one."""
            else:
                found = True
                value = domain_value

        if found:
            return value
        else:
            raise KeyError


class SettingCluster(
    MixinSettingClusterDoers, MixinSettingClusterGetters,
    AppsModuleLoaderMixin, TemplateCacheSourceMixin
):
    _loader_module_name = 'settings'

    def __init__(self, domains, name):
        self.domain_list = domains
        self.name = name
        self.namespace_dict = {}
        self.namespace_metadata = {}
        self.setting_dict = {}

        TemplateCacheSourceRegistry.register(source=self)

    def __str__(self):
        return self.name
