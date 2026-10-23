import json

from rest_framework.renderers import BaseRenderer


class EventStreamRenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''

        if isinstance(
            data, (bytes, str)
        ):
            return data

        return json.dumps(obj=data).encode('utf-8')
