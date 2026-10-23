from datetime import timedelta

from django.db import models
from django.utils.timezone import now

from .settings import setting_event_retention


class StreamEventManager(models.Manager):
    def enqueue(self, user, event_type, payload):
        return self.create(
            event_type=event_type, payload=payload, user=user
        )

    def stale_delete(self):
        cutoff = now() - timedelta(
            seconds=setting_event_retention.value
        )
        queryset = self.filter(datetime_created__lt=cutoff)
        queryset.delete()
