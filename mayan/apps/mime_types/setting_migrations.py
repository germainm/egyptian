from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)


class SettingMigrationMIMEType(SettingNamespaceMigration):
    def mime_type_backend_0001(self, value):
        return 'mayan.apps.mime_types.backends.file_command.MIMETypeBackendFileCommand'
