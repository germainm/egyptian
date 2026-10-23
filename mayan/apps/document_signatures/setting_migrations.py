from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.utils import smart_yaml_load


class DocumentSignaturesSettingMigration(SettingNamespaceMigration):
    def signatures_storage_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)
