import os
from pathlib import Path
import sys

from django.core.exceptions import ImproperlyConfigured
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

import mayan
from mayan.apps.authentication.literals import (
    DEFAULT_AUTHENTICATION_LOCKOUT_COOLOFF_TIME,
    DEFAULT_AUTHENTICATION_LOCKOUT_ENABLED,
    DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT,
    DEFAULT_AUTHENTICATION_LOCKOUT_PARAMETERS,
    DEFAULT_AUTHENTICATION_LOCKOUT_RESET_ON_SUCCESS
)
from mayan.apps.common.settings_utils import do_extra_settings_function_apply
from mayan.apps.rest_api.literals import API_VERSION
from mayan.apps.smart_settings.literals import COMMAND_NAME_SETTINGS_REVERT
from mayan.apps.smart_settings.utils import SettingNamespaceSingleton

from ..literals import (
    DEFAULT_SECRET_KEY, SECRET_KEY_FILENAME, SYSTEM_DIR, UPLOAD_TEMPORARY_DIR
)

BASE_DIR = Path(__file__).resolve().parent.parent

setting_namespace = SettingNamespaceSingleton(
    global_symbol_table=globals()
)


def get_databases_sqlite():
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(
                Path(MEDIA_ROOT, 'db.sqlite3')
            )
        }
    }


if COMMAND_NAME_SETTINGS_REVERT in sys.argv:
    setting_namespace.update_globals(only_critical=True)
    DATABASES = get_databases_sqlite()
else:
    setting_namespace.update_globals()

try:
    SECRET_KEY = os.environ['MAYAN_SECRET_KEY']
except KeyError:
    path_secret_key = Path(
        MEDIA_ROOT, SYSTEM_DIR, SECRET_KEY_FILENAME
    )
    try:
        with path_secret_key.open(mode='rb') as file_object:
            SECRET_KEY = file_object.read().strip()
    except FileNotFoundError:
        SECRET_KEY = DEFAULT_SECRET_KEY


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'rest_api_throttling': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}


AXES_COOLOFF_TIME = DEFAULT_AUTHENTICATION_LOCKOUT_COOLOFF_TIME
AXES_ENABLED = DEFAULT_AUTHENTICATION_LOCKOUT_ENABLED
AXES_FAILURE_LIMIT = DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT
AXES_LOCKOUT_PARAMETERS = DEFAULT_AUTHENTICATION_LOCKOUT_PARAMETERS
AXES_LOCKOUT_TEMPLATE = 'authentication/account_locked.html'
AXES_RESET_ON_SUCCESS = DEFAULT_AUTHENTICATION_LOCKOUT_RESET_ON_SUCCESS


INSTALLED_APPS = (
    'mayan.apps.events.apps.EventsApp',
    'mayan.apps.appearance.apps.AppearanceApp',
    'mayan.apps.appearance_bootstrap.apps.AppearanceBootstrapApp',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.forms',
    'django.contrib.staticfiles',
    'actstream',
    'axes',
    'corsheaders',
    'django_celery_beat',
    'formtools',
    'mozilla_django_oidc',
    'mptt',
    'rest_framework',
    'rest_framework.authtoken',
    'solo',
    'widget_tweaks',
    'mayan.apps.logging.apps.LoggingApp',
    'mayan.apps.task_manager.apps.TaskManagerApp',
    'mayan.apps.acls.apps.ACLsApp',
    'mayan.apps.user_management.apps.UserManagementApp',
    'mayan.apps.app_manager.apps.AppManagerAppConfig',
    'mayan.apps.authentication.apps.AuthenticationApp',
    'mayan.apps.authentication_attempts.apps.AuthenticationAttemptsApp',
    'mayan.apps.authentication_oidc.apps.AuthenticationOIDCApp',
    'mayan.apps.authentication_otp.apps.AuthenticationOTPApp',
    'mayan.apps.autoadmin.apps.AutoAdminAppConfig',
    'mayan.apps.backends.apps.BackendsApp',
    'mayan.apps.common.apps.CommonApp',
    'mayan.apps.converter.apps.ConverterApp',
    'mayan.apps.credentials.apps.CredentialsApp',
    'mayan.apps.credentials_google.apps.CredentialsGoogleApp',
    'mayan.apps.dashboards.apps.DashboardsApp',
    'mayan.apps.databases.apps.DatabasesApp',
    'mayan.apps.dependencies.apps.DependenciesApp',
    'mayan.apps.django_gpg.apps.DjangoGPGApp',
    'mayan.apps.documentation.apps.DocumentationApp',
    'mayan.apps.dynamic_search.apps.DynamicSearchApp',
    'mayan.apps.file_caching.apps.FileCachingAppConfig',
    'mayan.apps.forms.apps.FormsApp',
    'mayan.apps.fundraisers.apps.FundraisersAppConfig',
    'mayan.apps.icons.apps.IconsApp',
    'mayan.apps.locales.apps.LocalesApp',
    'mayan.apps.lock_manager.apps.LockManagerApp',
    'mayan.apps.messaging.apps.MessagingApp',
    'mayan.apps.mime_types.apps.MIMETypesApp',
    'mayan.apps.navigation.apps.NavigationApp',
    'mayan.apps.organizations.apps.OrganizationsApp',
    'mayan.apps.permissions.apps.PermissionsApp',
    'mayan.apps.platforms.apps.PlatformsApp',
    'mayan.apps.platforms_sentry.apps.PlatformsSentryApp',
    'mayan.apps.quotas.apps.QuotasApp',
    'mayan.apps.rest_api.apps.RESTAPIApp',
    'mayan.apps.server_side_events.apps.ServerSideEventsApp',
    'mayan.apps.service_workers.apps.ServiceWorkersApp',
    'mayan.apps.smart_settings.apps.SmartSettingsApp',
    'mayan.apps.storage.apps.StorageApp',
    'mayan.apps.templating.apps.TemplatingApp',
    'mayan.apps.views.apps.ViewsApp',
    'mayan.apps.announcements.apps.AnnouncementsApp',
    'mayan.apps.motd.apps.MOTDApp',
    'mayan.apps.documents.apps.DocumentsApp',
    'mayan.apps.cabinets.apps.CabinetsApp',
    'mayan.apps.checkouts.apps.CheckoutsApp',
    'mayan.apps.document_comments.apps.DocumentCommentsApp',
    'mayan.apps.document_downloads.apps.DocumentDownloadsApp',
    'mayan.apps.document_exports.apps.DocumentExportsApp',
    'mayan.apps.document_favorites.apps.DocumentFavoritesApp',
    'mayan.apps.document_indexing.apps.DocumentIndexingApp',
    'mayan.apps.document_parsing.apps.DocumentParsingApp',
    'mayan.apps.document_signatures.apps.DocumentSignaturesApp',
    'mayan.apps.document_states.apps.DocumentStatesApp',
    'mayan.apps.duplicates.apps.DuplicatesApp',
    'mayan.apps.file_metadata.apps.FileMetadataApp',
    'mayan.apps.file_metadata_clamav.apps.FileMetadataClamAVApp',
    'mayan.apps.file_metadata_eml.apps.FileMetadataEMLApp',
    'mayan.apps.file_metadata_exif.apps.FileMetadataEXIFApp',
    'mayan.apps.file_metadata_msg.apps.FileMetadataMSGApp',
    'mayan.apps.file_metadata_ollama.apps.FileMetadataOllamaApp',
    'mayan.apps.file_metadata_openai.apps.FileMetadataOpenAIApp',
    'mayan.apps.file_metadata_pypdf.apps.FileMetadataPyPDFApp',
    'mayan.apps.linking.apps.LinkingApp',
    'mayan.apps.mailer.apps.MailerApp',
    'mayan.apps.mayan_statistics.apps.StatisticsApp',
    'mayan.apps.metadata.apps.MetadataApp',
    'mayan.apps.mirroring.apps.MirroringApp',
    'mayan.apps.ocr.apps.OCRApp',
    'mayan.apps.redactions.apps.RedactionsApp',
    'mayan.apps.sequences.apps.SequencesApp',
    'mayan.apps.signature_captures.apps.SignatureCapturesApp',
    'mayan.apps.source_compressed.apps.SourceCompressedApp',
    'mayan.apps.source_interactive.apps.SourceInteractiveApp',
    'mayan.apps.source_periodic.apps.SourcePeriodicApp',
    'mayan.apps.source_emails.apps.SourceEmailsApp',
    'mayan.apps.source_sane_scanners.apps.SourceSaneScannersApp',
    'mayan.apps.source_staging_folders.apps.SourceStagingFoldersApp',
    'mayan.apps.source_staging_storages.apps.SourceStagingStorageApp',
    'mayan.apps.source_generated_files.apps.SourceGeneratedFileApp',
    'mayan.apps.source_stored_files.apps.SourceStoredFileApp',
    'mayan.apps.source_watch_folders.apps.SourceWatchFoldersApp',
    'mayan.apps.source_watch_storages.apps.SourceWatchStorageApp',
    'mayan.apps.source_web_forms.apps.SourceWebFormsApp',
    'mayan.apps.sources.apps.SourcesApp',
    'mayan.apps.tags.apps.TagsApp',
    'mayan.apps.web_links.apps.WebLinksApp',
    'drf_spectacular',
    'drf_spectacular_sidecar',
)

MIDDLEWARE = (
    'mayan.apps.logging.middleware.error_logging.ErrorLoggingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mayan.apps.locales.middleware.locales.UserLocaleProfileMiddleware',
    'mayan.apps.authentication.middleware.impersonate.ImpersonateMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mayan.apps.authentication.middleware.login_required.LoginRequiredMiddleware',
    'mayan.apps.views.middleware.ajax_redirect.AjaxRedirect',
    'axes.middleware.AxesMiddleware'
)

MESSAGE_STORAGE = 'mayan.apps.server_side_events.messages.storages.server_side_events.ServerSideEventStorage'

ROOT_URLCONF = 'mayan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ]
        }
    }
]

WSGI_APPLICATION = 'mayan.wsgi.application'


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'


LANGUAGES = (
    ('ar-eg', _(message='Arabic (Egypt)')),
    ('ar', _(message='Arabic')),
    ('bg', _(message='Bulgarian')),
    ('bg-bg', _(message='Bulgarian (Bulgaria)')),
    ('bo', _(message='Tibetan')),
    ('bs', _(message='Bosnian')),
    ('ca', _(message='Catalan')),
    ('cs', _(message='Czech')),
    ('da', _(message='Danish')),
    ('de', _(message='German')),
    ('de-at', _(message='German (Austria)')),
    ('de-de', _(message='German (Germany)')),
    ('el', _(message='Greek')),
    ('el-gr', _(message='Greek (Greece)')),
    ('en', _(message='English')),
    ('es', _(message='Spanish')),
    ('es-ec', _(message='Spanish (Ecuador)')),
    ('es-es', _(message='Spanish (Spain)')),
    ('es-mx', _(message='Spanish (Mexico)')),
    ('es-pr', _(message='Spanish (Puerto Rico)')),
    ('fa', _(message='Persian')),
    ('fa-ir', _(message='Persian (Iran)')),
    ('fr', _(message='French')),
    ('fr-fr', _(message='French (France)')),
    ('he-il', _(message='Hebrew (Israel)')),
    ('hu', _(message='Hungarian')),
    ('hu-sk', _(message='Hungarian (Slovakia)')),
    ('hu-hu', _(message='Hungarian (Hungary)')),
    ('hr', _(message='Croatian')),
    ('hy-am', _(message='Armenian (Armenia)')),
    ('id', _(message='Indonesian')),
    ('it', _(message='Italian')),
    ('ja', _(message='Japanese')),
    ('lv', _(message='Latvian')),
    ('mn-mn', _(message='Mongolian (Mongolia)')),
    ('nl', _(message='Dutch')),
    ('pl', _(message='Polish')),
    ('pt', _(message='Portuguese')),
    ('pt-br', _(message='Portuguese (Brazil)')),
    ('ro-ro', _(message='Romanian (Romania)')),
    ('ru', _(message='Russian')),
    ('ru-ru', _(message='Russian (Russia)')),
    ('sl', _(message='Slovenian')),
    ('sq', _(message='Albanian')),
    ('th', _(message='Thai')),
    ('tr', _(message='Turkish')),
    ('tr-tr', _(message='Turkish (Turkey)')),
    ('uk', _(message='Ukrainian')),
    ('uk-ua', _(message='Ukrainian (Ukraine)')),
    ('vi', _(message='Vietnamese')),
    ('zh-cn', _(message='Chinese (China)')),
    ('zh-hans', _(message='Chinese (Simplified)')),
    ('zh-tw', _(message='Chinese (Taiwan)'))
)

MEDIA_URL = 'media/'

SITE_ID = 1

STATIC_ROOT = os.environ.get(
    'MAYAN_STATIC_ROOT', Path(MEDIA_ROOT, 'static')
)


FILE_UPLOAD_TEMP_DIR_DEFAULT = Path(MEDIA_ROOT, UPLOAD_TEMPORARY_DIR)
FILE_UPLOAD_TEMP_DIR = os.environ.get(
    'MAYAN_FILE_UPLOAD_TEMP_DIR',
    FILE_UPLOAD_TEMP_DIR_DEFAULT
)

if 'MAYAN_FILE_UPLOAD_TEMP_DIR' not in os.environ:
    if not FILE_UPLOAD_TEMP_DIR_DEFAULT.is_dir():
        FILE_UPLOAD_TEMP_DIR = None

MEDIA_URL = 'media/'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'mayan.apps.views.finders.MayanAppDirectoriesFinder'
)

STORAGES = {}
STORAGES['staticfiles'] = {
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
}

TEST_RUNNER = 'mayan.apps.testing.runner.MayanTestRunner'

LOGIN_REQUIRED_EXEMPT_URLS = ()

SESSION_REFRESH_EXEMPT_URLS = ()


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'mayan.apps.authentication_attempts.authentication_classes.LoginAttemptTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ),
    'DEFAULT_PAGINATION_CLASS': 'mayan.apps.rest_api.pagination.MayanPageNumberPagination',
    'DEFAULT_SCHEMA_CLASS': 'mayan.apps.rest_api.schemas.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'mayan.apps.rest_api.throttling.MayanAnonRateThrottle',
        'mayan.apps.rest_api.throttling.MayanUserRateThrottle'
    ),
    'EXCEPTION_HANDLER': 'mayan.apps.rest_api.exception_handlers.mayan_exception_handler'
}


PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 5,
    'MARGIN_PAGES_DISPLAYED': 2
}


CELERY_ACCEPT_CONTENT = ('json',)
CELERY_BEAT_SCHEDULE = {}
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
CELERY_CONTROL_QUEUE_EXCLUSIVE = True
CELERY_DISABLE_RATE_LIMITS = True
CELERY_ENABLE_UTC = True
CELERY_EVENT_QUEUE_EXCLUSIVE = True
CELERY_RESULT_BACKEND_THREAD_SAFE = True
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_CREATE_MISSING_QUEUES = False
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_QUEUES = []
CELERY_TASK_ROUTES = {}
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'


CORS_ORIGIN_ALLOW_ALL = True


TIMEZONE_COOKIE_NAME = 'django_timezone'
TIMEZONE_SESSION_KEY = 'django_timezone'


SPECTACULAR_SETTINGS = {
    'TITLE': format_lazy('{title} API', title=mayan.__title__),
    'DESCRIPTION': mayan.__description__,
    'VERSION': 'v{}'.format(API_VERSION),
    'LICENSE': {
        'name': mayan.__license__
    },
    'ENUM_NAME_OVERRIDES': {
        'TimeDeltaUnitEnum': 'mayan.apps.common.literals.TIME_DELTA_UNIT_CHOICES'
    },
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SWAGGER_UI_SETTINGS': {
        'docExpansion': 'none'
    }
}


repeated_apps = tuple(
    set(COMMON_EXTRA_APPS_PRE).intersection(
        set(COMMON_EXTRA_APPS)
    )
)
if repeated_apps:
    raise ImproperlyConfigured(
        'Apps "{}" cannot be specified in `COMMON_EXTRA_APPS_PRE` and '
        '`COMMON_EXTRA_APPS` at the same time.'.format(
            ', '.join(
                tuple(repeated_apps)
            )
        )
    )

INSTALLED_APPS = tuple(
    COMMON_EXTRA_APPS_PRE or ()
) + INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + tuple(
    COMMON_EXTRA_APPS or ()
)

INSTALLED_APPS = [
    APP for APP in INSTALLED_APPS if APP not in (
        COMMON_DISABLED_APPS or ()
    )
]

if not DATABASES:
    if DATABASE_ENGINE:
        DATABASES = {
            'default': {
                'ENGINE': DATABASE_ENGINE,
                'NAME': DATABASE_NAME,
                'USER': DATABASE_USER,
                'PASSWORD': DATABASE_PASSWORD,
                'HOST': DATABASE_HOST,
                'PORT': DATABASE_PORT,
                'CONN_MAX_AGE': DATABASE_CONN_MAX_AGE
            }
        }
    else:
        DATABASES = get_databases_sqlite()


extra_settings_function_dotted_path_string = os.environ.get(
    'MAYAN_EXTRA_SETTINGS_FUNCTION_LIST', ''
)
INSTALLED_APPS, MIDDLEWARE = do_extra_settings_function_apply(
    installed_apps=INSTALLED_APPS, middleware=MIDDLEWARE,
    dotted_path_string=extra_settings_function_dotted_path_string
)
