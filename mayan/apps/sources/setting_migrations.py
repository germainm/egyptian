from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.setting_clusters import setting_cluster
from mayan.apps.smart_settings.utils import smart_yaml_load


class SourcesSettingMigration(SettingNamespaceMigration):
    def sources_staging_file_cache_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)

    def sources_cache_storage_backend_0002(self, value):
        setting = setting_cluster.get_setting(
            global_name='SOURCES_CACHE_STORAGE_BACKEND'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='SOURCES_STAGING_FILE_CACHE_STORAGE_BACKEND',
            value=value, value_fallback=setting.default
        )

    def sources_cache_storage_backend_arguments_0002(self, value):
        setting = setting_cluster.get_setting(
            global_name='SOURCES_CACHE_STORAGE_BACKEND_ARGUMENTS'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='SOURCES_STAGING_FILE_CACHE_STORAGE_BACKEND_ARGUMENTS',
            value=value, value_fallback=setting.default
        )

    def sources_backend_arguments_0003(self, value):
        if not isinstance(value, dict):
            return value

        try:
            keyword_arguments = value[
                'mayan.apps.sources.source_backends.SourceBackendSANEScanner'
            ]
        except KeyError:
            return value

        value_migrated = value.copy()

        del value_migrated[
            'mayan.apps.sources.source_backends.SourceBackendSANEScanner'
        ]

        value_migrated.setdefault(
            'mayan.apps.source_sane_scanners.source_backends.SourceBackendSANEScanner',
            keyword_arguments
        )

        return value_migrated
