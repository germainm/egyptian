from django.utils.translation import gettext_lazy as _

DEFAULT_SEQUENCE_VALUE_COUNT_MAXIMUM = 1000

ON_LIMIT_RAISE = 'raise'
ON_LIMIT_WRAP = 'wrap'

ON_LIMIT_CHOICES = (
    (
        ON_LIMIT_RAISE, _(message='Raise an error and consume nothing')
    ),
    (
        ON_LIMIT_WRAP, _(message='Wrap around to the first position')
    )
)

WORKFLOW_ACTION_SEQUENCE_CONTEXT_NAMESPACE = 'sequences'
