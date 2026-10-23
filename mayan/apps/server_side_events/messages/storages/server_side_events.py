from django.contrib.messages.storage.fallback import FallbackStorage

from ...classes import ServerEventStreamBackend

from .literals import EVENT_TYPE_TOAST


class ServerSideEventStorage(FallbackStorage):
    def _store(self, messages, response, *args, **kwargs):
        user = getattr(self.request, 'user', None)

        if user is not None and user.is_authenticated and messages:
            backend = ServerEventStreamBackend.get_instance()

            for message in messages:
                backend.enqueue(
                    data={
                        'level': message.level,
                        'message': str(message.message),
                        'tags': message.tags
                    }, event_type=EVENT_TYPE_TOAST, user=user
                )

            messages = []

        return super()._store(messages, response, *args, **kwargs)
