from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import StreamEventManager


class StreamEvent(models.Model):
    user = models.ForeignKey(
        on_delete=models.CASCADE, related_name='server_side_events',
        to=settings.AUTH_USER_MODEL, verbose_name=_(message='User')
    )
    event_type = models.CharField(
        db_index=True, max_length=128, verbose_name=_(message='Event type')
    )
    payload = models.TextField(
        blank=True, verbose_name=_(message='Payload')
    )
    datetime_created = models.DateTimeField(
        auto_now_add=True, db_index=True,
        verbose_name=_(message='Date and time created')
    )

    objects = StreamEventManager()

    class Meta:
        ordering = ('id',)
        verbose_name = _(message='Stream event')
        verbose_name_plural = _(message='Stream events')

    def __str__(self):
        return '{}: {}'.format(self.user, self.event_type)
