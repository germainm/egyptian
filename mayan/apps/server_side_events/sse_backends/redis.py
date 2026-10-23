import json

from django.utils.translation import gettext_lazy as _

from ..classes import ServerEvent, ServerEventStreamBackend
from ..literals import EVENT_FETCH_MAXIMUM


class RedisServerEventStreamBackend(ServerEventStreamBackend):
    label = _(message='Redis')

    def __init__(
        self, url='redis://localhost:6379/0', key_prefix='mayan:sse:',
        maximum_length=1024, **kwargs
    ):
        import redis

        self.client = redis.Redis.from_url(url=url)
        self.key_prefix = key_prefix
        self.maximum_length = maximum_length

    def _get_key(self, user):
        return '{}{}'.format(self.key_prefix, user.pk)

    def enqueue(self, user, event_type, data):
        name = self._get_key(user=user)
        data = json.dumps(obj=data)

        fields = {'data': data, 'event_type': event_type}

        self.client.xadd(
            approximate=True, fields=fields, maxlen=self.maximum_length,
            name=name
        )

    def get_initial_cursor(self, user):
        try:
            name = self._get_key(user=user)
            stream_info = self.client.xinfo_stream(name=name)
        except Exception:
            return '0-0'
        else:
            return stream_info['last-generated-id'].decode('utf-8')

    def get_events(self, user, cursor):
        cursor = cursor or '0-0'

        key = self._get_key(user=user)
        stream = {key: cursor}

        result = self.client.xread(count=EVENT_FETCH_MAXIMUM, streams=stream)

        events = []
        new_cursor = cursor

        for stream_name, entries in result:
            for entry_id, fields in entries:
                new_cursor = entry_id.decode('utf-8')
                data = json.loads(
                    s=fields[b'data']
                )
                event_type = fields[b'event_type'].decode('utf-8')
                server_event = ServerEvent(
                    data=data, event_type=event_type, id=new_cursor
                )

                events.append(server_event)

        return events, new_cursor
