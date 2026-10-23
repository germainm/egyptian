import json

from django.core.cache import caches
from django.utils.translation import gettext_lazy as _

from ..classes import ServerEvent, ServerEventStreamBackend
from ..literals import EVENT_FETCH_MAXIMUM


class CacheServerEventStreamBackend(ServerEventStreamBackend):
    label = _(message='Cache')

    def __init__(
        self, cache_name='default', key_prefix='mayan_sse', timeout=600,
        **kwargs
    ):
        self.cache = caches[cache_name]
        self.key_prefix = key_prefix
        self.timeout = timeout

    def _get_counter_key(self, user):
        return '{}:counter:{}'.format(self.key_prefix, user.pk)

    def _get_event_key(self, user, event_id):
        return '{}:event:{}:{}'.format(self.key_prefix, user.pk, event_id)

    def get_initial_cursor(self, user):
        key = self._get_counter_key(user=user)
        return self.cache.get(key=key) or 0

    def enqueue(self, user, event_type, data):
        counter_key = self._get_counter_key(user=user)

        self.cache.add(key=counter_key, value=0, timeout=None)
        event_id = self.cache.incr(key=counter_key)

        key = self._get_event_key(user=user, event_id=event_id)
        value = json.dumps(
            obj={'data': data, 'event_type': event_type}
        )
        self.cache.set(key=key, timeout=self.timeout, value=value)

    def get_events(self, user, cursor):
        cursor = int(cursor or 0)
        key = self._get_counter_key(user=user)
        latest = self.cache.get(key=key) or 0

        events = []
        new_cursor = cursor

        event_id = cursor
        while event_id < latest and len(events) < EVENT_FETCH_MAXIMUM:
            event_id = event_id + 1

            key = self._get_event_key(user=user, event_id=event_id)
            raw_value = self.cache.get(key=key)
            new_cursor = event_id

            if raw_value is not None:
                stored = json.loads(s=raw_value)
                events.append(
                    ServerEvent(
                        data=stored['data'],
                        event_type=stored['event_type'], id=event_id
                    )
                )

        return events, new_cursor
