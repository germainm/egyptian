from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.setting_clusters import setting_cluster


class DocumentFavoritesSettingMigration(SettingNamespaceMigration):
    def document_favorites_count_0001(self, value):
        setting = setting_cluster.get_setting(
            global_name='DOCUMENT_FAVORITES_COUNT'
        )

        return self.get_value_renamed(
            global_name=setting.global_name,
            global_name_old='DOCUMENTS_FAVORITE_COUNT', value=value,
            value_fallback=setting.default
        )
