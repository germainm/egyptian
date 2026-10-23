from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='Sequences'), name='sequences'
)

event_sequence_created = namespace.add_event_type(
    label=_(message='Sequence created'), name='sequence_created'
)
event_sequence_edited = namespace.add_event_type(
    label=_(message='Sequence edited'), name='sequence_edited'
)
event_sequence_exhausted = namespace.add_event_type(
    label=_(message='Sequence exhausted'), name='sequence_exhausted'
)
event_sequence_reset = namespace.add_event_type(
    label=_(message='Sequence reset'), name='sequence_reset'
)
event_sequence_used = namespace.add_event_type(
    label=_(message='Sequence used'), name='sequence_used'
)
