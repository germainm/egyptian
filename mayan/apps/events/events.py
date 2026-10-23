from django.utils.translation import gettext_lazy as _

from .classes import EventTypeNamespace
from .literals import (
    EVENT_EVENTS_CLEARED_NAME, EVENT_EVENTS_EXPORTED_NAME,
    EVENT_TYPE_NAMESPACE_NAME
)

namespace = EventTypeNamespace(
    label=_(message='Events'), name=EVENT_TYPE_NAMESPACE_NAME
)

event_events_cleared = namespace.add_event_type(
    label=_(message='Events cleared'), name=EVENT_EVENTS_CLEARED_NAME
)
event_events_exported = namespace.add_event_type(
    label=_(message='Events exported'), name=EVENT_EVENTS_EXPORTED_NAME
)
