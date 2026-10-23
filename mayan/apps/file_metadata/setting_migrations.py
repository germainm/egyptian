from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.utils import smart_yaml_load


class FileMetadataSettingMigration(SettingNamespaceMigration):
    def file_metadata_drivers_arguments_0001(self, value):
        return smart_yaml_load(value=value)
