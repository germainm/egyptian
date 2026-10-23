import logging

from django.apps import apps
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.user_management.permissions import permission_group_view

from .classes import Permission, PermissionNamespace
from .events import event_role_edited

logger = logging.getLogger(name=__name__)


class RoleBusinessLogicMixin:
    def get_group_count(self, user):
        return self.get_groups(user=user).count()

    def get_groups(self, user):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        return AccessControlList.objects.restrict_queryset(
            permission=permission_group_view, queryset=self.groups.all(),
            user=user
        )
    get_group_count.short_description = _(message='Group count')

    def get_permission_count(self):
        return self.permissions.count()
    get_permission_count.short_description = _(message='Permission count')

    def grant(self, permission):
        self.permissions.add(permission.stored_permission)

    def groups_add(self, queryset, user=None):
        for model_instance in queryset:
            self.groups.add(model_instance)
            event_role_edited.commit(
                action_object=model_instance, actor=user, target=self
            )

    def groups_remove(self, queryset, user=None):
        for model_instance in queryset:
            self.groups.remove(model_instance)
            event_role_edited.commit(
                action_object=model_instance, actor=user, target=self
            )

    def permissions_add(self, queryset, user=None):
        for model_instance in queryset:
            self.permissions.add(model_instance)
            event_role_edited.commit(
                action_object=model_instance, actor=user or self.user,
                target=self
            )

    def permissions_remove(self, queryset, user=None):
        for model_instance in queryset:
            self.permissions.remove(model_instance)
            event_role_edited.commit(
                action_object=model_instance, actor=user or self.user,
                target=self
            )

    def revoke(self, permission):
        self.permissions.remove(permission.stored_permission)


class StoredPermissionBusinessLogicMixin:
    @property
    def label(self):
        try:
            permission = self.volatile_permission
        except KeyError:
            return _(
                message='Unknown or obsolete permission: %s'
            ) % self.name
        else:
            return permission.label

    @property
    def namespace_label(self):
        try:
            permission_namespace = PermissionNamespace.get(
                name=self.namespace
            )
        except KeyError:
            return _(
                message='Unknown or obsolete permission namespace: %s'
            ) % self.namespace
        else:
            return permission_namespace.label

    def user_has_this(self, user):
        Role = apps.get_model(app_label='permissions', model_name='Role')

        if user.is_superuser or user.is_staff:
            logger.debug(
                'Permission "%s" granted to user "%s" as super user or '
                'staff', self, user
            )
            return True

        if not user.is_authenticated:
            return False

        if Role.objects.filter(groups__user=user, permissions=self).exists():
            return True
        else:
            logger.debug(
                'Fallthru: Permission "%s" not granted to user "%s"',
                self, user
            )
            return False

    @cached_property
    def volatile_permission(self):
        return Permission.get(pk=self.volatile_permission_id)

    @cached_property
    def volatile_permission_id(self):
        return '{}.{}'.format(self.namespace, self.name)
