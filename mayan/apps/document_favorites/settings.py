from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import DEFAULT_DOCUMENT_FAVORITES_COUNT
from .setting_migrations import DocumentFavoritesSettingMigration

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Document favorites'),
    migration_class=DocumentFavoritesSettingMigration,
    name='document_favorites', version='0002'
)

setting_favorite_count = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENT_FAVORITES_COUNT,
    global_name='DOCUMENT_FAVORITES_COUNT', help_text=_(
        message='Maximum number of favorite documents to remember per user.'
    )
)
