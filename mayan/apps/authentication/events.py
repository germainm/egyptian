from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='Authentication'), name='authentication'
)

event_user_account_lockout_reset = namespace.add_event_type(
    label=_(message='User account lockout reset'),
    name='user_account_lockout_reset'
)
event_user_impersonation_ended = namespace.add_event_type(
    label=_(message='User impersonation ended'), name='user_impersonation_ended'
)
event_user_impersonation_started = namespace.add_event_type(
    label=_(message='User impersonation started'), name='user_impersonation_started'
)
event_user_logged_in = namespace.add_event_type(
    label=_(message='User logged in'), name='user_logged_in'
)
event_user_logged_out = namespace.add_event_type(
    label=_(message='User logged out'), name='user_logged_out'
)
