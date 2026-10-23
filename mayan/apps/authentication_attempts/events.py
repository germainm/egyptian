from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='Authentication attempts'),
    name='authentication_attempts'
)

event_user_login_failed = namespace.add_event_type(
    label=_(message='User login failed'), name='user_login_failed'
)
event_user_login_succeeded = namespace.add_event_type(
    label=_(message='User login succeeded'), name='user_login_succeeded'
)
