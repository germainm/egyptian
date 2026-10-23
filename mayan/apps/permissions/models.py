from django.contrib.auth.models import Group
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_role_created, event_role_edited
from .managers import RoleManager, StoredPermissionManager
from .model_mixins import (
    RoleBusinessLogicMixin, StoredPermissionBusinessLogicMixin
)


class Role(ExtraDataModelMixin, RoleBusinessLogicMixin, models.Model):
    _ordering_fields = ('label',)

    label = models.CharField(
        help_text=_(message='A short text describing the role.'),
        max_length=128, unique=True, verbose_name=_(message='Label')
    )
    permissions = models.ManyToManyField(
        related_name='roles', to='StoredPermission',
        verbose_name=_(message='Permissions')
    )
    groups = models.ManyToManyField(
        related_name='roles', to=Group, verbose_name=_(message='Groups')
    )

    objects = RoleManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Role')
        verbose_name_plural = _(message='Roles')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(viewname='permissions:role_list')

    def natural_key(self):
        return (self.label,)
    natural_key.dependencies = ['auth.Group', 'permissions.StoredPermission']

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_role_created,
            'target': 'self'
        },
        edited={
            'event': event_role_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class StoredPermission(StoredPermissionBusinessLogicMixin, models.Model):
    namespace = models.CharField(
        max_length=64, verbose_name=_(message='Namespace')
    )
    name = models.CharField(
        max_length=64, verbose_name=_(message='Name')
    )

    objects = StoredPermissionManager()

    class Meta:
        ordering = ('namespace',)
        unique_together = ('namespace', 'name')
        verbose_name = _(message='Permission')
        verbose_name_plural = _(message='Permissions')

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse(
            viewname='permissions:stored_permission_detail', kwargs={
                'stored_permission_id': self.pk
            }
        )

    def natural_key(self):
        return (self.namespace, self.name)
