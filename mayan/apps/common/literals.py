from django.conf import settings
from django.utils.translation import gettext_lazy as _

COMMAND_NAME_COMMON_INITIAL_SETUP = 'common_initial_setup'
COMMAND_NAME_COMMON_PERFORM_UPGRADE = 'common_perform_upgrade'
COMMAND_NAME_MIGRATE = 'migrate'

DEFAULT_COMMON_DISABLED_APPS = settings.COMMON_DISABLED_APPS
DEFAULT_COMMON_DISABLE_LOCAL_STORAGE = False
DEFAULT_COMMON_EXTRA_APPS = settings.COMMON_EXTRA_APPS
DEFAULT_COMMON_EXTRA_APPS_PRE = settings.COMMON_EXTRA_APPS_PRE
DEFAULT_COMMON_HOME_VIEW = 'common:home'
DEFAULT_COMMON_HOME_VIEW_DASHBOARD_NAME = 'user'
DEFAULT_COMMON_PROJECT_TITLE = None

DJANGO_SQLITE_BACKEND = 'django.db.backends.sqlite3'

MARKDOWN_ATTRIBUTES_ALLOWED = {
    'a': {'href'}
}

MARKDOWN_EXTENSION_LIST = ('nl2br', 'tables')

MESSAGE_DEPRECATION_WARNING = _(
    message='This feature has been deprecated and will be removed in a future '
    'version.'
)

TIME_DELTA_UNIT_DAYS = 'days'
TIME_DELTA_UNIT_HOURS = 'hours'
TIME_DELTA_UNIT_MINUTES = 'minutes'

TIME_DELTA_UNIT_CHOICES = (
    (TIME_DELTA_UNIT_DAYS, _(message='Days')),
    (TIME_DELTA_UNIT_HOURS, _(message='Hours')),
    (TIME_DELTA_UNIT_MINUTES, _(message='Minutes'))
)

URL_BOOK = 'https://www.mayan-edms.com/book/'
URL_DOCUMENTATION = 'https://docs.mayan-edms.com'
URL_FORUM = 'https://forum.mayan-edms.com'
URL_KNOWLEDGE_BASE = 'https://forum.mayan-edms.com/t/availability-of-the-new-knowledge-base/883'
URL_MAILING_LIST = 'https://list.mayan-edms.com/subscription/form'
URL_RELEASE_NOTES = 'https://docs.mayan-edms.com/releases/index.html'
URL_SOURCE_CODE = 'https://gitlab.com/mayan-edms/mayan-edms'
URL_STORE = 'https://teespring.com/stores/mayan-edms'
URL_SUPPORT = 'https://www.mayan-edms.com/support/'
