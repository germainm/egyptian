import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)
from mayan.apps.permissions.models import Role, StoredPermission

from .events import event_acl_created, event_acl_deleted
from .managers import AccessControlListManager
from .model_mixins import AccessControlListBusinessLogicMixin

logger = logging.getLogger(name=__name__)


class AccessControlList(
    AccessControlListBusinessLogicMixin, ExtraDataModelMixin, models.Model
):
    _ordering_fields = ('object_id',)

    content_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='object_content_type',
        to=ContentType, verbose_name=_(message='Content type')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_(message='Object ID')
    )
    content_object = GenericForeignKey(
        ct_field='content_type', fk_field='object_id'
    )
    permissions = models.ManyToManyField(
        blank=True, related_name='acls', to=StoredPermission,
        verbose_name=_(message='Permissions')
    )
    role = models.ForeignKey(
        help_text=_(
            message='Role to which the access is granted for the specified '
            'object.'
        ), on_delete=models.CASCADE, related_name='acls', to=Role,
        verbose_name=_(message='Role')
    )

    objects = AccessControlListManager()

    class Meta:
        ordering = ('pk',)
        unique_together = ('content_type', 'object_id', 'role')
        verbose_name = _(message='Access entry')
        verbose_name_plural = _(message='Access entries')

    def __str__(self):
        return _(
            message='Role "%(role)s" permission\'s for "%(object)s"'
        ) % {
            'object': self.content_object,
            'role': self.role
        }

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_acl_deleted,
        target='content_object'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            kwargs={'acl_id': self.pk}, viewname='acls:acl_permissions'
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'content_object',
            'event': event_acl_created,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class GlobalAccessControlListProxy(AccessControlList):
    class Meta:
        proxy = True
