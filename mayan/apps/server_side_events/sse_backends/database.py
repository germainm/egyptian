import json

from django.apps import apps
from django.db import connection
from django.utils.translation import gettext_lazy as _

from ..classes import ServerEvent, ServerEventStreamBackend
from ..literals import EVENT_FETCH_MAXIMUM


class DatabaseServerEventStreamBackend(ServerEventStreamBackend):
    label = _(message='Database')

    def _get_model(self):
        return apps.get_model(
            app_label='server_side_events', model_name='StreamEvent'
        )

    def enqueue(self, user, event_type, data):
        model = self._get_model()

        payload = json.dumps(obj=data)
        model.objects.enqueue(
            event_type=event_type, payload=payload, user=user
        )

    def get_initial_cursor(self, user):
        model = self._get_model()

        queryset = model.objects.filter(user=user).order_by('id')
        last_event = queryset.last()

        return last_event.pk if last_event else 0

    def get_events(self, user, cursor):
        model = self._get_model()

        queryset = model.objects.filter(user=user)

        if cursor:
            queryset = queryset.filter(
                pk__gt=int(cursor)
            )

        events = []
        new_cursor = cursor

        for instance in queryset.order_by('id')[:EVENT_FETCH_MAXIMUM]:
            data = json.loads(s=instance.payload or 'null')

            server_event = ServerEvent(
                data=data, event_type=instance.event_type, id=instance.pk
            )

            events.append(server_event)

            new_cursor = instance.pk

        return events, new_cursor

    def on_idle(self):
        if not connection.in_atomic_block:
            connection.close()
