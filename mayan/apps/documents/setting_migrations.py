from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.setting_clusters import setting_cluster
from mayan.apps.smart_settings.utils import smart_yaml_load

from .literals import (
    DEFAULT_DOCUMENTS_STORAGE_BACKEND,
    DEFAULT_DOCUMENTS_STORAGE_BACKEND_ARGUMENTS
)


class DocumentsSettingMigration(SettingNamespaceMigration):
    def documents_cache_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)

    def documents_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)

    def documents_file_page_image_cache_storage_backend_0003(self, value):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_CACHE_STORAGE_BACKEND', value=value,
            value_fallback=setting.default
        )

    def documents_file_page_image_cache_storage_backend_arguments_0003(
        self, value
    ):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_CACHE_STORAGE_BACKEND_ARGUMENTS',
            value=value, value_fallback=setting.default
        )

    def documents_file_storage_backend_0003(self, value):
        return self.get_value_renamed(
            global_name='DOCUMENTS_FILE_STORAGE_BACKEND',
            global_name_old='DOCUMENTS_STORAGE_BACKEND', value=value,
            value_fallback=DEFAULT_DOCUMENTS_STORAGE_BACKEND
        )

    def documents_file_storage_backend_arguments_0003(self, value):
        return self.get_value_renamed(
            global_name='DOCUMENTS_FILE_STORAGE_BACKEND_ARGUMENTS',
            global_name_old='DOCUMENTS_STORAGE_BACKEND_ARGUMENTS',
            value=value,
            value_fallback=DEFAULT_DOCUMENTS_STORAGE_BACKEND_ARGUMENTS
        )

    def documents_recently_accessed_count_0002(self, value):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_RECENTLY_ACCESSED_COUNT'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_RECENT_ACCESS_COUNT', value=value,
            value_fallback=setting.default
        )

    def documents_recently_created_count_0002(self, value):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_RECENTLY_CREATED_COUNT'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_RECENT_ADDED_COUNT', value=value,
            value_fallback=setting.default
        )

    def documents_version_page_image_cache_storage_backend_0003(self, value):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_CACHE_STORAGE_BACKEND', value=value,
            value_fallback=setting.default
        )

    def documents_version_page_image_cache_storage_backend_arguments_0003(
        self, value
    ):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_CACHE_STORAGE_BACKEND_ARGUMENTS',
            value=value, value_fallback=setting.default
        )
