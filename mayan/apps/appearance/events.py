from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='Appearance'), name='appearance'
)

event_theme_created = namespace.add_event_type(
    label=_(message='Theme created'), name='theme_created'
)
event_theme_edited = namespace.add_event_type(
    label=_(message='Theme edited'), name='theme_edited'
)
event_user_theme_settings_edited = namespace.add_event_type(
    label=_(message='User theme edited'), name='user_theme_edited'
)

event_user_setting_edited = namespace.add_event_type(
    label=_(message='User setting edited'), name='user_setting_edited'
)
