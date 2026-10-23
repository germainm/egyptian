from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='User management'), name='user_management'
)

event_group_created = namespace.add_event_type(
    label=_(message='Group created'), name='group_created'
)
event_group_edited = namespace.add_event_type(
    label=_(message='Group edited'), name='group_edited'
)

event_user_created = namespace.add_event_type(
    label=_(message='User created'), name='user_created'
)
event_user_edited = namespace.add_event_type(
    label=_(message='User edited'), name='user_edited'
)

event_user_logged_in = namespace.add_event_type(
    label=_(message='User logged in'), name='user_logged_in'
)
event_user_logged_out = namespace.add_event_type(
    label=_(message='User logged out'), name='user_logged_out'
)
