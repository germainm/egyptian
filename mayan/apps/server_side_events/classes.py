import json

from django.core.exceptions import ImproperlyConfigured

from mayan.apps.backends.classes import BaseBackend

from .settings import setting_backend, setting_backend_arguments


class ServerEvent:
    def __init__(self, id, event_type, data):
        self.id = id
        self.event_type = event_type
        self.data = data

    def render(self):
        return 'id: {}\nevent: {}\ndata: {}\n\n'.format(
            self.id, self.event_type, json.dumps(obj=self.data)
        )


class ServerEventStreamBackend(BaseBackend):
    _loader_module_name = 'sse_backends'

    @classmethod
    def get_instance(cls, extra_kwargs=None):
        kwargs = (
            setting_backend_arguments.value or {}
        ).copy()
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        try:
            backend_class = cls.get(name=setting_backend.value)
        except KeyError:
            raise ImproperlyConfigured(
                'Unknown or unregistered server side events backend: '
                '`{}`.'.format(setting_backend.value)
            )

        return backend_class(**kwargs)

    def enqueue(self, user, event_type, data):
        raise NotImplementedError

    def get_initial_cursor(self, user):
        return None

    def get_events(self, user, cursor):
        raise NotImplementedError

    def on_idle(self):
        pass
