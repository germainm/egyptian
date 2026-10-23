from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from .classes import Setting
from .literals import NAMESPACE_VERSION_INITIAL


class SettingNamespaceMetaclass(type):
    _registry = {}

    def __call__(mcls, cluster, name, **kwargs):
        if name in mcls._registry:
            raise ImproperlyConfigured(
                'Setting namespace `{}` already exists.'.format(name)
            )
        else:
            instance = super().__call__(
                cluster=cluster, name=name, **kwargs
            )
            mcls._registry[name] = instance

        return instance

    @classmethod
    def unregister(mcls, instance):
        for setting in instance.get_setting_list():
            Setting.unregister(instance=setting)

        mcls._registry.pop(instance.name, None)


class SettingNamespace(metaclass=SettingNamespaceMetaclass):
    def __init__(
        self, cluster, name, label, migration_class=None,
        version=NAMESPACE_VERSION_INITIAL
    ):
        self.cluster = cluster
        self.migration_class = migration_class
        self.name = name
        self.label = label
        self.setting_dict = {}
        self.version = version

        self.do_cluster_join()

    def __str__(self):
        return force_str(s=self.label)


    def do_cache_invalidate(self):
        for setting in self.setting_dict.values():
            setting.do_cache_invalidate()

    def do_cluster_join(self):
        cluster = self.get_cluster()
        cluster.do_namespace_join(namespace=self)

    def do_ready(self):
        self.do_version_set()

        self.do_settings_ready()

        self.do_settings_migrate()

    def do_setting_add(self, **kwargs):
        setting = Setting(namespace=self, **kwargs)
        self.setting_dict[setting.global_name] = setting

        return setting

    def do_setting_join(self, setting):
        self.setting_dict[setting.global_name] = setting
        cluster = self.get_cluster()
        cluster.do_setting_join(setting=setting)

    def do_setting_remove(self, setting):
        self.setting_dict.pop(setting.global_name)
        cluster = self.get_cluster()
        cluster.do_setting_remove(setting=setting)

    def do_settings_migrate(self):
        if self.migration_class:
            for setting in self.get_setting_list():
                migration_instance = self.migration_class(namespace=self)
                migration_instance.do_setting_migrate(setting=setting)

    def do_settings_ready(self):
        for setting in self.get_setting_list():
            setting.do_ready()

    def do_version_set(self):
        cluster = self.get_cluster()
        metadata = {'version': self.version}
        cluster.do_namespace_metadata_update(
            namespace=self, metadata=metadata
        )


    def get_cluster(self):
        return self.cluster

    def get_setting(self, global_name):
        return self.setting_dict[global_name]

    def get_setting_list(self):
        return sorted(
            self.setting_dict.values(), key=lambda x: x.global_name
        )

    def get_settings_as_data(self, filter_term, value_pending_map=None):
        result = {}

        for setting in self.get_setting_list():
            selected = (
                filter_term and filter_term.lower() in setting.global_name.lower()
            )

            if not filter_term or selected:
                value = setting.get_value_pending(
                    value_pending_map=value_pending_map
                )
                result[setting.global_name] = value

        return result


SettingNamespace.verbose_name = _(message='Settings namespace')
