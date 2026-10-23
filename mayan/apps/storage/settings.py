from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_DOWNLOAD_FILE_EXPIRATION_INTERVAL,
    DEFAULT_SHARED_UPLOADED_FILE_EXPIRATION_INTERVAL,
    DEFAULT_STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM,
    DEFAULT_STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM,
    DEFAULT_STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM,
    DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE,
    DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE_ARGUMENTS,
    DEFAULT_STORAGE_SHARED_STORAGE, DEFAULT_STORAGE_SHARED_STORAGE_ARGUMENTS,
    DEFAULT_STORAGE_TEMPORARY_DIRECTORY
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Storage'), name='storage'
)

setting_compressed_file_input_size_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM,
    global_name='STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM', help_text=_(
        message='Maximum size in bytes of a compressed-archive input file '
        '(EML, MSG, PDF, TAR, ZIP, and friends) that will be attempted '
        'to parse. Files larger than this are rejected before being read '
        'into memory, to prevent memory-exhaustion attacks. Set to 0 to '
        'disable.'
    )
)
setting_compressed_file_member_size_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM,
    global_name='STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM', help_text=_(
        message='Maximum size in bytes of a single member inside a '
        'compressed archive. Members whose declared (uncompressed) size '
        'exceeds this value are rejected before being decompressed. '
        'Set to 0 to disable.'
    )
)
setting_compressed_file_compression_ratio_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM,
    global_name='STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM',
    help_text=_(
        message='Maximum ratio of uncompressed size to compressed size '
        'permitted for a compressed archive. Ratios above this value '
        'are characteristic of zip-bomb / tar-bomb payloads and are '
        'rejected. For formats that store a compressed size per member '
        '(ZIP), the ratio is applied to each member. For formats that '
        'compress the whole archive as a single unit (TAR, and its '
        'gzip and bzip2 variants), no per member compressed size '
        'exists, so the ratio is applied to the archive as a whole: '
        'the declared size of all members combined against the size of '
        'the archive file. Raise this value if legitimate archives of '
        'highly compressible content are being rejected. Set to 0 to '
        'disable.'
    )
)
setting_download_file_expiration_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOWNLOAD_FILE_EXPIRATION_INTERVAL,
    global_name='DOWNLOAD_FILE_EXPIRATION_INTERVAL', help_text=_(
        message='Time in seconds, after which download files will be deleted.'
    )
)
setting_download_file_storage = setting_namespace.do_setting_add(
    default=DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE,
    global_name='STORAGE_DOWNLOAD_FILE_STORAGE', help_text=_(
        message='A storage backend that all workers can use to generate and '
        'hold files for download.'
    )
)
setting_download_file_storage_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE_ARGUMENTS,
    global_name='STORAGE_DOWNLOAD_FILE_STORAGE_ARGUMENTS',
    help_text=_(
        message='Keyword arguments to pass to the '
        '`STORAGE_DOWNLOAD_FILE_STORAGE` backend.'
    )
)
setting_shared_storage = setting_namespace.do_setting_add(
    default=DEFAULT_STORAGE_SHARED_STORAGE,
    global_name='STORAGE_SHARED_STORAGE', help_text=_(
        message='A storage backend that all workers can use to share files.'
    )
)
setting_shared_storage_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_STORAGE_SHARED_STORAGE_ARGUMENTS,
    global_name='STORAGE_SHARED_STORAGE_ARGUMENTS',
    help_text=_(
        message='Keyword arguments to pass to the `STORAGE_SHARED_STORAGE` '
        'backend.'
    )
)
setting_temporary_directory = setting_namespace.do_setting_add(
    default=DEFAULT_STORAGE_TEMPORARY_DIRECTORY,
    global_name='STORAGE_TEMPORARY_DIRECTORY', help_text=_(
        message='Temporary directory used site wide to store thumbnails, '
        'previews and temporary files.'
    )
)
setting_shared_uploaded_file_expiration_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_SHARED_UPLOADED_FILE_EXPIRATION_INTERVAL,
    global_name='SHARED_UPLOADED_FILE_EXPIRATION_INTERVAL', help_text=_(
        message='Time in seconds, after which temporary uploaded files will '
        'be deleted.'
    )
)
