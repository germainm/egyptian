from django.utils.translation import gettext_lazy as _

DATABASE_MINIMUM_ID = 1

DEFAULT_CREATE_BULK_BATCH_SIZE = 100

DEFAULT_QUERYSET_ITERATOR_CHUNK_SIZE = 2000

DJANGO_IGNORE_APP_MIGRATIONS = set(
    ('auth',)
)

DJANGO_POSITIVE_INTEGER_FIELD_MAX_VALUE = 2147483647

DJANGO_SQLITE_BACKEND = 'django.db.backends.sqlite3'

MESSAGE_SQLITE_WARNING = _(
    message='Your database backend is set to use SQLite. SQLite should only be used '
    'for development and testing, not for production.'
)
