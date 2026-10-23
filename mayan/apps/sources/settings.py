from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_SOURCES_BACKEND_ARGUMENTS, DEFAULT_SOURCES_CACHE_MAXIMUM_SIZE,
    DEFAULT_SOURCES_CACHE_STORAGE_BACKEND,
    DEFAULT_SOURCES_CACHE_STORAGE_BACKEND_ARGUMENTS
)
from .setting_callbacks import callback_update_source_cache_size
from .setting_migrations import SourcesSettingMigration

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Sources'), migration_class=SourcesSettingMigration,
    name='sources', version='0004'
)

setting_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_SOURCES_BACKEND_ARGUMENTS,
    global_name='SOURCES_BACKEND_ARGUMENTS', help_text=_(
        message='Arguments to use when creating source backends.'
    )
)

setting_source_cache_maximum_size = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_SOURCES_CACHE_MAXIMUM_SIZE,
    global_name='SOURCES_CACHE_MAXIMUM_SIZE',
    help_text=_(
        message='The threshold at which the SOURCES_CACHE_STORAGE_BACKEND '
        'will start deleting the oldest source cache files. Specify the size '
        'in bytes.'
    ), post_edit_function=callback_update_source_cache_size
)
setting_source_cache_storage_backend = setting_namespace.do_setting_add(
    global_name='SOURCES_CACHE_STORAGE_BACKEND',
    default=DEFAULT_SOURCES_CACHE_STORAGE_BACKEND, help_text=_(
        message='Path to the Storage subclass used to store cached source '
        'image files.'
    )
)
setting_source_cache_storage_backend_arguments = setting_namespace.do_setting_add(
    global_name='SOURCES_CACHE_STORAGE_BACKEND_ARGUMENTS',
    default=DEFAULT_SOURCES_CACHE_STORAGE_BACKEND_ARGUMENTS,
    help_text=_(
        message='Arguments to pass to the '
        '`SOURCES_SOURCE_CACHE_STORAGE_BACKEND`.'
    )
)
