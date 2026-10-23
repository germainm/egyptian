from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from actstream.models import Action

from .managers import (
    EventSubscriptionManager, NotificationManager,
    ObjectEventSubscriptionManager, StoredEventTypeManager
)
from .model_mixins import (
    NotificationBusinessLogicMixin, StoredEventTypeBusinessLogicMixin
)


class StoredEventType(StoredEventTypeBusinessLogicMixin, models.Model):
    _ordering_fields = ('name',)

    name = models.CharField(
        max_length=64, unique=True, verbose_name=_(message='Name')
    )

    objects = StoredEventTypeManager()

    class Meta:
        verbose_name = _(message='Stored event type')
        verbose_name_plural = _(message='Stored event types')

    def __str__(self):
        return str(self.label)


class EventSubscription(models.Model):
    user = models.ForeignKey(
        db_index=True, on_delete=models.CASCADE,
        related_name='event_subscriptions', to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )
    stored_event_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='event_subscriptions',
        to=StoredEventType, verbose_name=_(message='Event type')
    )

    objects = EventSubscriptionManager()

    class Meta:
        verbose_name = _(message='Event subscription')
        verbose_name_plural = _(message='Event subscriptions')

    def __str__(self):
        return str(self.stored_event_type)


class Notification(NotificationBusinessLogicMixin, models.Model):
    _ordering_fields = ('read',)

    user = models.ForeignKey(
        db_index=True, on_delete=models.CASCADE,
        related_name='notifications', to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )
    action = models.ForeignKey(
        on_delete=models.CASCADE, related_name='notifications', to=Action,
        verbose_name=_(message='Action')
    )
    read = models.BooleanField(
        default=False, verbose_name=_(message='Read')
    )

    objects = NotificationManager()

    class Meta:
        ordering = ('-action__timestamp',)
        verbose_name = _(message='Notification')
        verbose_name_plural = _(message='Notifications')

    def __str__(self):
        return str(self.action)


class ObjectEventSubscription(models.Model):
    content_type = models.ForeignKey(
        on_delete=models.CASCADE, to=ContentType,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(
        ct_field='content_type',
        fk_field='object_id',
    )
    user = models.ForeignKey(
        db_index=True, on_delete=models.CASCADE,
        related_name='object_subscriptions', to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )
    stored_event_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='object_subscriptions',
        to=StoredEventType, verbose_name=_(message='Event type')
    )

    objects = ObjectEventSubscriptionManager()

    class Meta:
        ordering = ('pk',)
        verbose_name = _(message='Object event subscription')
        verbose_name_plural = _(message='Object event subscriptions')

    def __str__(self):
        return str(self.stored_event_type)
