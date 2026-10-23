from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_CONVERTER_ASSET_CACHE_MAXIMUM_SIZE,
    DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND,
    DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND_ARGUMENTS,
    DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND,
    DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND_ARGUMENTS,
    DEFAULT_CONVERTER_COMMAND_TIMEOUT,
    DEFAULT_CONVERTER_GRAPHICS_BACKEND,
    DEFAULT_CONVERTER_GRAPHICS_BACKEND_ARGUMENTS,
    DEFAULT_CONVERTER_IMAGE_CACHE_TIME,
    DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_CONCURRENCY,
    DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_RATE,
    DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_ATTEMPT_MAXIMUM,
    DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_INITIAL,
    DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_MAXIMUM,
    DEFAULT_CONVERTER_IMAGE_GENERATION_MAX_RETRIES,
    DEFAULT_CONVERTER_IMAGE_GENERATION_RETRY_DELAY,
    DEFAULT_CONVERTER_IMAGE_GENERATION_TIMEOUT,
    DEFAULT_CONVERTER_LOAD_TRUNCATED_IMAGES
)
from .setting_callbacks import callback_update_asset_cache_size
from .setting_migrations import ConvertSettingMigration
from .setting_validators import (
    validation_function_integer_minimum_one,
    validation_function_integer_minimum_zero
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Converter'), migration_class=ConvertSettingMigration,
    name='converter', version='0002'
)


setting_asset_cache_maximum_size = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_ASSET_CACHE_MAXIMUM_SIZE,
    global_name='CONVERTER_ASSET_CACHE_MAXIMUM_SIZE',
    help_text=_(
        message='The threshold at which the '
        'CONVERTER_ASSET_CACHE_STORAGE_BACKEND '
        'will start deleting the oldest asset cache files. '
        'Specify the size in bytes.'
    ), post_edit_function=callback_update_asset_cache_size
)
setting_asset_cache_storage_backend = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND,
    global_name='CONVERTER_ASSET_CACHE_STORAGE_BACKEND', help_text=_(
        message='Path to the Storage subclass to use when storing the '
        'cached asset files.'
    )
)
setting_asset_cache_storage_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND_ARGUMENTS,
    global_name='CONVERTER_ASSET_CACHE_STORAGE_BACKEND_ARGUMENTS',
    help_text=_(
        message='Arguments to pass to the '
        'CONVERTER_ASSET_CACHE_STORAGE_BACKEND.'
    )
)
setting_asset_storage_backend = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND,
    global_name='CONVERTER_ASSET_STORAGE_BACKEND', help_text=_(
        message='Path to the Storage subclass to use when storing assets.'
    )
)
setting_asset_storage_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND_ARGUMENTS,
    global_name='CONVERTER_ASSET_STORAGE_BACKEND_ARGUMENTS', help_text=_(
        message='Arguments to pass to the CONVERTER_ASSET_STORAGE_BACKEND.'
    )
)
setting_graphics_backend = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_GRAPHICS_BACKEND,
    global_name='CONVERTER_GRAPHICS_BACKEND', help_text=_(
        message='Graphics conversion backend to use.'
    )
)
setting_graphics_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_GRAPHICS_BACKEND_ARGUMENTS,
    global_name='CONVERTER_GRAPHICS_BACKEND_ARGUMENTS', help_text=_(
        message='Configuration options for the graphics conversion backend. '
        'The `libreoffice_arguments` entry adds command-line arguments to '
        'every LibreOffice invocation. The `libreoffice_environment` entry '
        'is a mapping of environment variables passed to the LibreOffice '
        'subprocess.'
    )
)
setting_image_cache_time = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_IMAGE_CACHE_TIME,
    global_name='CONVERTER_IMAGE_CACHE_TIME',
    help_text=_(
        message='Time in seconds that the browser should cache the '
        'supplied image.'
    )
)
setting_image_carousel_request_concurrency = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_CONCURRENCY,
    global_name='CONVERTER_IMAGE_CAROUSEL_REQUEST_CONCURRENCY',
    help_text=_(
        message='Maximum number of document page images the browser will '
        'request from the API at the same time while scrolling the '
        'document image carousel.'
    ), validation_function=validation_function_integer_minimum_one
)
setting_image_carousel_request_rate = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_RATE,
    global_name='CONVERTER_IMAGE_CAROUSEL_REQUEST_RATE',
    help_text=_(
        message='Maximum number of document page image requests per second '
        'the browser will send to the API while scrolling the document '
        'image carousel. A value of 0 derives the rate at runtime from 80% '
        'of the REST API authenticated user throttling rate, so the browser '
        'stays under the limit the API enforces. Any other value overrides '
        'that derived default.'
    ), validation_function=validation_function_integer_minimum_zero
)
setting_image_carousel_retry_attempt_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_ATTEMPT_MAXIMUM,
    global_name='CONVERTER_IMAGE_CAROUSEL_RETRY_ATTEMPT_MAXIMUM',
    help_text=_(
        message='Maximum number of times the browser will retry a document '
        'page image request that the API refuses before showing the error '
        'image.'
    ), validation_function=validation_function_integer_minimum_zero
)
setting_image_carousel_retry_delay_initial = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_INITIAL,
    global_name='CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_INITIAL',
    help_text=_(
        message='Initial time in milliseconds the browser waits before '
        'retrying a refused document page image request. The wait grows '
        'exponentially with each attempt. Used only when the API does not '
        'provide a `Retry-After` header.'
    ), validation_function=validation_function_integer_minimum_one
)
setting_image_carousel_retry_delay_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_MAXIMUM,
    global_name='CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_MAXIMUM',
    help_text=_(
        message='Maximum time in milliseconds the browser will wait between '
        'retries of a refused document page image request.'
    ), validation_function=validation_function_integer_minimum_one
)
setting_image_generation_max_retries = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_IMAGE_GENERATION_MAX_RETRIES,
    global_name='CONVERTER_IMAGE_GENERATION_MAX_RETRIES',
    help_text=_(
        message='Maximum number of retries before giving up. A retry '
        'happens when the image is already being produced elsewhere, so '
        'this number multiplied by the retry delay is how long the task '
        'waits for that work to finish. A value of None means the task '
        'will retry forever.'
    )
)
setting_image_generation_retry_delay = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_IMAGE_GENERATION_RETRY_DELAY,
    global_name='CONVERTER_IMAGE_GENERATION_RETRY_DELAY',
    help_text=_(
        message='Time in seconds between the attempts of the image '
        'generation task. The interval is constant because the wait ends '
        'when another process finishes producing the same image, and an '
        'interval that grew would leave a finished image unread.'
    )
)
setting_image_generation_timeout = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_CONVERTER_IMAGE_GENERATION_TIMEOUT,
    global_name='CONVERTER_IMAGE_GENERATION_TIMEOUT',
    help_text=_(
        message='Time in seconds after which the image generation task '
        'will stop running and raise an error.'
    )
)
setting_load_truncated_images = setting_namespace.do_setting_add(
    default=DEFAULT_CONVERTER_LOAD_TRUNCATED_IMAGES,
    global_name='CONVERTER_LOAD_TRUNCATED_IMAGES',
    help_text=_(
        message='Whether or not to load truncated image files.'
    )
)


def get_command_timeout():
    graphics_backend_arguments = setting_graphics_backend_arguments.value

    return graphics_backend_arguments.get(
        'command_timeout', DEFAULT_CONVERTER_COMMAND_TIMEOUT
    )
