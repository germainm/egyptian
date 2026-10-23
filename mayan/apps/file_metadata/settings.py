from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_FILE_METADATA_AUTO_PROCESS,
    DEFAULT_FILE_METADATA_DRIVERS_ARGUMENTS,
    DEFAULT_FILE_METADATA_MAXIMUM_VALUE_LENGTH
)
from .setting_migrations import FileMetadataSettingMigration

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='File metadata'),
    migration_class=FileMetadataSettingMigration, name='file_metadata',
    version='0002'
)
setting_auto_process = setting_namespace.do_setting_add(
    choices=('false', 'true'), default=DEFAULT_FILE_METADATA_AUTO_PROCESS,
    global_name='FILE_METADATA_AUTO_PROCESS', help_text=_(
        message='Set new document types to perform file metadata processing '
        'automatically by default.'
    )
)
setting_drivers_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_FILE_METADATA_DRIVERS_ARGUMENTS,
    global_name='FILE_METADATA_DRIVERS_ARGUMENTS', help_text=_(
        message='Arguments to pass to the drivers.'
    )
)
setting_maximum_value_length = setting_namespace.do_setting_add(
    default=DEFAULT_FILE_METADATA_MAXIMUM_VALUE_LENGTH,
    global_name='FILE_METADATA_MAXIMUM_VALUE_LENGTH', help_text=_(
        message='Maximum number of characters to store for each file '
        'metadata entry value. Drivers processing big documents can emit '
        'very long values (embedded descriptions, keyword lists, AI '
        'generated text) that inflate the database and the search index '
        'without adding search value. Longer values are truncated to this '
        'limit. Leave empty to store values without a length limit.'
    )
)
