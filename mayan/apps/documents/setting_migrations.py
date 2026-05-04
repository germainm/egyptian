from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.settings import setting_cluster
from mayan.apps.smart_settings.utils import smart_yaml_load

from .literals import (
    DEFAULT_DOCUMENTS_STORAGE_BACKEND,
    DEFAULT_DOCUMENTS_STORAGE_BACKEND_ARGUMENTS
)


class DocumentsSettingMigration(SettingNamespaceMigration):
    """
    0001 to 0002: Backend arguments are no longer quoted but YAML valid
                  too. Changed in version 3.3.
    0002 to 0003: Setting DOCUMENTS_RECENT_ADDED_COUNT renamed to
                  DOCUMENTS_RECENTLY_CREATED_COUNT,
                  DOCUMENTS_RECENT_ADDED_COUNT renamed to
                  DOCUMENTS_RECENTLY_CREATED_COUNT. Changed in version 4.0.
    0003 to 0004: New settings for document file storage, file page image
                  cache and version page image cache added and made to take
                  their initial settings from existing
                  DOCUMENTS_CACHE_STORAGE_BACKEND,
                  DOCUMENTS_CACHE_STORAGE_BACKEND_ARGUMENTS,
                  DOCUMENTS_STORAGE_BACKEND, and
                  DOCUMENTS_STORAGE_BACKEND_ARGUMENTS settings.
    """
    def documents_cache_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)

    def documents_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)

    def documents_file_page_image_cache_storage_backend_0003(self, value):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_CACHE_STORAGE_BACKEND'
            )
        except KeyError:
            return setting.default
        else:
            return value

    def documents_file_page_image_cache_storage_backend_arguments_0003(
        self, value
    ):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_CACHE_STORAGE_BACKEND_ARGUMENTS'
            )
        except KeyError:
            return setting.default
        else:
            return value

    def documents_file_storage_backend_0003(self, value):
        # Si la valeur courante est deja definie (non None), la conserver.
        # Cela evite d'ecraser une valeur configuree dans config.yml.
        if value is not None:
            return value
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_STORAGE_BACKEND'
            )
        except KeyError:
            return DEFAULT_DOCUMENTS_STORAGE_BACKEND
        else:
            return value

    def documents_file_storage_backend_arguments_0003(self, value):
        # Si la valeur courante est deja definie (non None), la conserver.
        if value is not None:
            return value
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_STORAGE_BACKEND_ARGUMENTS'
            )
        except KeyError:
            return DEFAULT_DOCUMENTS_STORAGE_BACKEND_ARGUMENTS
        else:
            return value

    def documents_recently_accessed_count_0002(self, value):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_RECENTLY_ACCESSED_COUNT'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_RECENT_ACCESS_COUNT'
            )
        except KeyError:
            return setting.default
        else:
            return value

    def documents_recently_created_count_0002(self, value):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_RECENTLY_CREATED_COUNT'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_RECENT_ADDED_COUNT'
            )
        except KeyError:
            return setting.default
        else:
            return value

    def documents_version_page_image_cache_storage_backend_0003(self, value):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_CACHE_STORAGE_BACKEND'
            )
        except KeyError:
            return setting.default
        else:
            return value

    def documents_version_page_image_cache_storage_backend_arguments_0003(
        self, value
    ):
        # Get the setting by its new global name.
        setting = setting_cluster.get_setting(
            global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS'
        )
        # Load the value from the setting's old global name.
        try:
            value, domain_dict = setting_cluster.get_domains_value(
                key='DOCUMENTS_CACHE_STORAGE_BACKEND_ARGUMENTS'
            )
        except KeyError:
            return setting.default
        else:
            return value
