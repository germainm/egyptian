from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.thumbnail_click_behaviors import (
    ThumbnailClickBehaviorBackend
)
from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_DOCUMENTS_DISPLAY_HEIGHT, DEFAULT_DOCUMENTS_DISPLAY_WIDTH,
    DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_MAXIMUM_SIZE,
    DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND,
    DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS,
    DEFAULT_DOCUMENTS_FILE_STORAGE_BACKEND,
    DEFAULT_DOCUMENTS_FILE_STORAGE_BACKEND_ARGUMENTS,
    DEFAULT_DOCUMENTS_HASH_BLOCK_SIZE, DEFAULT_DOCUMENTS_LIST_THUMBNAIL_WIDTH,
    DEFAULT_DOCUMENTS_PREVIEW_HEIGHT, DEFAULT_DOCUMENTS_PREVIEW_WIDTH,
    DEFAULT_DOCUMENTS_PRINT_HEIGHT, DEFAULT_DOCUMENTS_PRINT_WIDTH,
    DEFAULT_DOCUMENTS_RECENTLY_ACCESSED_COUNT,
    DEFAULT_DOCUMENTS_RECENTLY_CREATED_COUNT, DEFAULT_DOCUMENTS_ROTATION_STEP,
    DEFAULT_DOCUMENTS_STUBS_DELETE_TASK_INTERVAL,
    DEFAULT_DOCUMENTS_THUMBNAIL_CLICK_BEHAVIOR,
    DEFAULT_DOCUMENTS_THUMBNAIL_HEIGHT, DEFAULT_DOCUMENTS_THUMBNAIL_WIDTH,
    DEFAULT_DOCUMENTS_TRASH_PERIOD_CHECK_TASK_INTERVAL,
    DEFAULT_DOCUMENTS_TRASHED_DELETE_PERIODS_CHECK_TASK_INTERVAL,
    DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_MAXIMUM_SIZE,
    DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND,
    DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS,
    DEFAULT_DOCUMENTS_ZOOM_MAX_LEVEL, DEFAULT_DOCUMENTS_ZOOM_MIN_LEVEL,
    DEFAULT_DOCUMENTS_ZOOM_PERCENT_STEP, DEFAULT_LANGUAGE,
    DEFAULT_LANGUAGE_CODES
)
from .setting_callbacks import (
    callback_update_document_file_page_image_cache_size,
    callback_update_document_version_page_image_cache_size
)
from .setting_data_types import setting_value_to_optional_int
from .setting_migrations import DocumentsSettingMigration

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Documents'), migration_class=DocumentsSettingMigration,
    name='documents', version='0004'
)

setting_display_height = setting_namespace.do_setting_add(
    data_type=setting_value_to_optional_int,
    default=DEFAULT_DOCUMENTS_DISPLAY_HEIGHT,
    global_name='DOCUMENTS_DISPLAY_HEIGHT', help_text=_(
        message='Optional height in pixels of the document page image used '
        'for interactive display. Leave empty to calculate the height from '
        '`DOCUMENTS_DISPLAY_WIDTH` while preserving the aspect ratio.'
    )
)
setting_display_width = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_DISPLAY_WIDTH,
    global_name='DOCUMENTS_DISPLAY_WIDTH',
    help_text=_(
        message='Width in pixels of the document page image used for '
        'interactive display. Larger values improve quality but increase '
        'processing time and cache storage.'
    )
)
setting_document_file_page_image_cache_maximum_size = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_MAXIMUM_SIZE,
    global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_MAXIMUM_SIZE',
    help_text=_(
        message='Maximum size in bytes of the '
        '`DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND`. When this limit '
        'is exceeded, the storage backend will start deleting the oldest '
        'cached page images.'
    ), post_edit_function=callback_update_document_file_page_image_cache_size
)
setting_document_file_storage_backend = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_FILE_STORAGE_BACKEND,
    global_name='DOCUMENTS_FILE_STORAGE_BACKEND', help_text=_(
        message='Dotted path to the storage subclass to used to store '
        'document files.'
    )
)
setting_document_file_storage_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_FILE_STORAGE_BACKEND_ARGUMENTS,
    global_name='DOCUMENTS_FILE_STORAGE_BACKEND_ARGUMENTS', help_text=_(
        message='Keyword arguments to pass to '
        '`DOCUMENTS_FILE_STORAGE_BACKEND`.'
    )
)
setting_document_file_page_image_cache_storage_backend = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND,
    global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND', help_text=_(
        message='Dotted path to the storage subclass used to store the '
        'cached document file page images.'
    )
)
setting_document_file_page_image_cache_storage_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS,
    global_name='DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS',
    help_text=_(
        message='Keyword arguments to pass to '
        '`DOCUMENTS_FILE_PAGE_IMAGE_CACHE_STORAGE_BACKEND`.'
    )
)
setting_hash_block_size = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_HASH_BLOCK_SIZE,
    global_name='DOCUMENTS_HASH_BLOCK_SIZE', help_text=_(
        message='Block size in bytes used when calculating a document file '
        'checksum. Use 0 to disable block reads and hash the entire file '
        'in a single pass (loads the file into memory).'
    )
)
setting_language = setting_namespace.do_setting_add(
    default=DEFAULT_LANGUAGE, global_name='DOCUMENTS_LANGUAGE',
    help_text=_(message='Default documents language (in ISO639-3 format).')
)
setting_language_codes = setting_namespace.do_setting_add(
    default=DEFAULT_LANGUAGE_CODES, global_name='DOCUMENTS_LANGUAGE_CODES',
    help_text=_(
        message='List of supported document languages (in ISO639-3 format).'
    )
)
setting_document_version_page_image_cache_maximum_size = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_MAXIMUM_SIZE,
    global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_MAXIMUM_SIZE',
    help_text=_(
        message='Maximum size in bytes of the '
        '`DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND`. When this '
        'limit is exceeded, the storage backend will start deleting the '
        'oldest cached version page images.'
    ), post_edit_function=callback_update_document_version_page_image_cache_size
)
setting_document_version_page_image_cache_storage_backend = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND,
    global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND',
    help_text=_(
        message='Dotted path to the storage subclass used to store cached '
        'document version page images.'
    )
)
setting_document_version_page_image_cache_storage_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS,
    global_name='DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND_ARGUMENTS',
    help_text=_(
        message='Keyword arguments to pass to '
        '`DOCUMENTS_VERSION_PAGE_IMAGE_CACHE_STORAGE_BACKEND`.'
    ),
)
setting_preview_height = setting_namespace.do_setting_add(
    data_type=setting_value_to_optional_int,
    default=DEFAULT_DOCUMENTS_PREVIEW_HEIGHT,
    global_name='DOCUMENTS_PREVIEW_HEIGHT',
    help_text=_(
        message='Optional height in pixels of the document preview image. '
        'Leave empty to calculate the height from `DOCUMENTS_PREVIEW_WIDTH` '
        'while preserving the aspect ratio.'
    )
)
setting_preview_width = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_PREVIEW_WIDTH,
    global_name='DOCUMENTS_PREVIEW_WIDTH',
    help_text=_(
        message='Width in pixels of the document preview image. '
        'Larger values improve quality but increase processing time and '
        'cache storage.'
    )
)
setting_print_height = setting_namespace.do_setting_add(
    data_type=setting_value_to_optional_int,
    default=DEFAULT_DOCUMENTS_PRINT_HEIGHT,
    global_name='DOCUMENTS_PRINT_HEIGHT',
    help_text=_(
        message='Optional height in pixels of the document page image '
        'generated for printing. Leave empty to calculate the height from '
        '`DOCUMENTS_PRINT_WIDTH` while preserving the aspect ratio.'
    )
)
setting_print_width = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_PRINT_WIDTH,
    global_name='DOCUMENTS_PRINT_WIDTH',
    help_text=_(
        message='Width in pixels of the document page image generated for '
        'printing. Larger values improve quality but increase processing '
        'time and cache storage.'
    )
)
setting_recently_accessed_document_count = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_RECENTLY_ACCESSED_COUNT,
    global_name='DOCUMENTS_RECENTLY_ACCESSED_COUNT', help_text=_(
        message='Maximum number of recently accessed documents to remember '
        'per user (viewed, created, or edited).'
    )
)
setting_recently_created_document_count = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_RECENTLY_CREATED_COUNT,
    global_name='DOCUMENTS_RECENTLY_CREATED_COUNT', help_text=_(
        message='Maximum number of recently created documents to show.'
    )
)
setting_rotation_step = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_ROTATION_STEP,
    global_name='DOCUMENTS_ROTATION_STEP', help_text=_(
        message='Rotation step in degrees applied each time the user '
        'rotates a page.'
    )
)
setting_task_document_type_document_trash_periods_check_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_TRASH_PERIOD_CHECK_TASK_INTERVAL,
    global_name='DOCUMENTS_TRASH_PERIOD_CHECK_TASK_INTERVAL',
    help_text=_(
        message='Interval in seconds between runs of the document trashing '
        'check task.'
    )
)
setting_task_document_type_document_stubs_delete_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_STUBS_DELETE_TASK_INTERVAL,
    global_name='DOCUMENTS_STUBS_DELETE_TASK_INTERVAL',
    help_text=_(
        message='Interval in seconds between runs of the document stub '
        'prune task.'
    )
)
setting_task_trashed_document_delete_periods_check_interval = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_DOCUMENTS_TRASHED_DELETE_PERIODS_CHECK_TASK_INTERVAL,
    global_name='DOCUMENTS_TRASHED_DOCUMENT_DELETE_PERIODS_CHECK_TASK_INTERVAL',
    help_text=_(
        message='Interval in seconds between runs of the trashed document '
        'deletion task.'
    )
)
setting_thumbnail_height = setting_namespace.do_setting_add(
    data_type=setting_value_to_optional_int,
    default=DEFAULT_DOCUMENTS_THUMBNAIL_HEIGHT,
    global_name='DOCUMENTS_THUMBNAIL_HEIGHT', help_text=_(
        message='Optional height in pixels of the document thumbnail image. '
        'Leave empty to calculate the height from `DOCUMENTS_THUMBNAIL_WIDTH` '
        'while preserving the aspect ratio.'
    )
)
setting_thumbnail_width = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_THUMBNAIL_WIDTH,
    global_name='DOCUMENTS_THUMBNAIL_WIDTH', help_text=_(
        message='Width in pixels of the document thumbnail image.'
    )
)
setting_thumbnail_click_behavior = setting_namespace.do_setting_add(
    choices=ThumbnailClickBehaviorBackend.get_setting_choices,
    default=DEFAULT_DOCUMENTS_THUMBNAIL_CLICK_BEHAVIOR,
    global_name='DOCUMENTS_THUMBNAIL_CLICK_BEHAVIOR', help_text=_(
        message='Behavior triggered when a document thumbnail is clicked. '
        'The `image_preview` behavior shows the enlarged image; the '
        '`route_to_document` behavior opens the document. Additional '
        'behaviors registered by other apps are also available.'
    )
)
setting_thumbnail_list_width = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_LIST_THUMBNAIL_WIDTH,
    global_name='DOCUMENTS_LIST_THUMBNAIL_WIDTH', help_text=_(
        message='Width in pixels of the document thumbnail image when shown '
        'in list view mode.'
    )
)
setting_zoom_max_level = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_ZOOM_MAX_LEVEL,
    global_name='DOCUMENTS_ZOOM_MAX_LEVEL', help_text=_(
        message='Maximum zoom level (percent) allowed when viewing a '
        'document page.'
    )
)
setting_zoom_min_level = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_ZOOM_MIN_LEVEL,
    global_name='DOCUMENTS_ZOOM_MIN_LEVEL', help_text=_(
        message='Minimum zoom level (percent) allowed when viewing a '
        'document page.'
    )
)
setting_zoom_percent_step = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_DOCUMENTS_ZOOM_PERCENT_STEP,
    global_name='DOCUMENTS_ZOOM_PERCENT_STEP', help_text=_(
        message='Zoom step (percent) applied each time the user zooms in '
        'or out.'
    )
)
