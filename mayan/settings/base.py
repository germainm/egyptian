import os
from pathlib import Path
import sys

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.literals import COMMAND_NAME_SETTINGS_REVERT
from mayan.apps.smart_settings.utils import SettingNamespaceSingleton

from ..literals import DEFAULT_SECRET_KEY, SECRET_KEY_FILENAME, SYSTEM_DIR

BASE_DIR = Path(__file__).resolve().parent.parent

setting_namespace = SettingNamespaceSingleton(
    global_symbol_table=globals()
)


def get_databases_sqlite():
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(
                Path(MEDIA_ROOT, 'db.sqlite3')  # NOQA: F821
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
        MEDIA_ROOT, SYSTEM_DIR, SECRET_KEY_FILENAME  # NOQA: F821
    )
    try:
        with path_secret_key.open(mode='rb') as file_object:  # NOQA: F821
            SECRET_KEY = file_object.read().strip()
    except FileNotFoundError:
        SECRET_KEY = DEFAULT_SECRET_KEY

# Caching

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'rest_api_throttling': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

# Application definition

INSTALLED_APPS = (
    # Placed at the top so it can preload all events defined by apps.
    'mayan.apps.events.apps.EventsApp',
    # Placed at the top so it can override any template.
    'mayan.apps.appearance.apps.AppearanceApp',
    'mayan.apps.appearance_bootstrap.apps.AppearanceBootstrapApp',
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.forms',
    'django.contrib.staticfiles',
    # 3rd party.
    'actstream',
    'corsheaders',
    'django_celery_beat',
    'formtools',
    'mozilla_django_oidc',
    'mptt',
    'rest_framework',
    'rest_framework.authtoken',
    'solo',
    'stronghold',
    'widget_tweaks',
    # Base apps
    # Moved to the top to ensure Mayan app logging is initialized and
    # available as soon as possible.
    'mayan.apps.logging.apps.LoggingApp',
    # Task manager goes to the top to ensure all queues are created before any
    # other app tries to use them.
    'mayan.apps.task_manager.apps.TaskManagerApp',
    'mayan.apps.acls.apps.ACLsApp',
    # User management app must go before authentication to ensure the Group
    # and User models are properly setup using runtime methods.
    'mayan.apps.user_management.apps.UserManagementApp',
    'mayan.apps.app_manager.apps.AppManagerAppConfig',
    'mayan.apps.authentication.apps.AuthenticationApp',
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
    'mayan.apps.platforms_docker.apps.PlatformsDockerApp',
    'mayan.apps.platforms_forge.apps.PlatformsForgeApp',
    'mayan.apps.platforms_gitlab.apps.PlatformsGitlabApp',
    'mayan.apps.platforms_sentry.apps.PlatformsSentryApp',
    'mayan.apps.quotas.apps.QuotasApp',
    'mayan.apps.rest_api.apps.RESTAPIApp',
    'mayan.apps.smart_settings.apps.SmartSettingsApp',
    'mayan.apps.storage.apps.StorageApp',
    'mayan.apps.templating.apps.TemplatingApp',
    'mayan.apps.views.apps.ViewsApp',
    # Obsolete apps. Need to remain to allow migrations to execute.
    'mayan.apps.announcements.apps.AnnouncementsApp',
    'mayan.apps.motd.apps.MOTDApp',
    # Document apps.
    # The documents app must be first since Django does not support signal
    # priorities.
    # https://docs.djangoproject.com/en/4.2/topics/signals/#listening-to-signals
    # https://code.djangoproject.com/ticket/16547
    'mayan.apps.documents.apps.DocumentsApp',
    'mayan.apps.cabinets.apps.CabinetsApp',
    'mayan.apps.checkouts.apps.CheckoutsApp',
    'mayan.apps.document_comments.apps.DocumentCommentsApp',
    'mayan.apps.document_downloads.apps.DocumentDownloadsApp',
    'mayan.apps.document_exports.apps.DocumentExportsApp',
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
    # Placed after rest_api to allow template overriding.
    'drf_yasg',
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
    'stronghold.middleware.LoginRequiredMiddleware',
    'mayan.apps.views.middleware.ajax_redirect.AjaxRedirect'
)

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

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    }
]

# Internationalization. Do not change these, doing so will break your
# installation.

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

# ------------ Custom settings section ----------

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
    'MAYAN_STATIC_ROOT', Path(MEDIA_ROOT, 'static')  # NOQA: F821
)

MEDIA_URL = 'media/'

# Silence warning and keep default for the time being.
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
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

# ---------- Django REST framework -----------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ),
    'DEFAULT_PAGINATION_CLASS': 'mayan.apps.rest_api.pagination.MayanPageNumberPagination',
    'DEFAULT_THROTTLE_CLASSES': (
        'mayan.apps.rest_api.throttling.MayanAnonRateThrottle',
        'mayan.apps.rest_api.throttling.MayanUserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/second',
        'user': '10/second'
    },
    'EXCEPTION_HANDLER': 'mayan.apps.rest_api.exception_handlers.mayan_exception_handler'
}

# --------- Pagination --------

PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 5,
    'MARGIN_PAGES_DISPLAYED': 2
}

# ----------- Celery ----------

CELERY_ACCEPT_CONTENT = ('json',)
CELERY_BEAT_SCHEDULE = {}
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
CELERY_DISABLE_RATE_LIMITS = True
CELERY_ENABLE_UTC = True
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_DEFAULT_QUEUE = 'celery'
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_QUEUES = []
CELERY_TASK_ROUTES = {}
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# ------------ CORS ------------

CORS_ORIGIN_ALLOW_ALL = True

# ------ Timezone --------

TIMEZONE_COOKIE_NAME = 'django_timezone'
TIMEZONE_SESSION_KEY = 'django_timezone'

# ----- Stronghold -------

STRONGHOLD_PUBLIC_URLS = (r'^/favicon\.ico$',)

# ----- Swagger --------

SWAGGER_SETTINGS = {
    'DEFAULT_INFO': 'rest_api.schemas.openapi_info',
    'DEFAULT_MODEL_DEPTH': 1,
    'DOC_EXPANSION': 'None'
}

# ------ End -----

BASE_INSTALLED_APPS = INSTALLED_APPS

for app in INSTALLED_APPS:
    if 'mayan.apps.{}'.format(app) in BASE_INSTALLED_APPS:
        raise ImproperlyConfigured(
            'Update the app references in the file config.yml as detailed '
            'in https://docs.mayan-edms.com/releases/3.2.html#backward-incompatible-changes'
        )

repeated_apps = tuple(
    set(COMMON_EXTRA_APPS_PRE).intersection(  # NOQA: F821
        set(COMMON_EXTRA_APPS)  # NOQA: F821
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
    COMMON_EXTRA_APPS_PRE or ()  # NOQA: F821
) + INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + tuple(
    COMMON_EXTRA_APPS or ()  # NOQA: F821
)

INSTALLED_APPS = [
    APP for APP in INSTALLED_APPS if APP not in (
        COMMON_DISABLED_APPS or ()  # NOQA: F821
    )
]

if not DATABASES:
    if DATABASE_ENGINE:  # NOQA: F821
        DATABASES = {
            'default': {
                'ENGINE': DATABASE_ENGINE,  # NOQA: F821
                'NAME': DATABASE_NAME,  # NOQA: F821
                'USER': DATABASE_USER,  # NOQA: F821
                'PASSWORD': DATABASE_PASSWORD,  # NOQA: F821
                'HOST': DATABASE_HOST,  # NOQA: F821
                'PORT': DATABASE_PORT,  # NOQA: F821
                'CONN_MAX_AGE': DATABASE_CONN_MAX_AGE  # NOQA: F821
            }
        }
    else:
        DATABASES = get_databases_sqlite()
