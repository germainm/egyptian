from django.apps import apps
from django.utils.translation import gettext_lazy as _

from .events import event_acl_edited


class AccessControlListBusinessLogicMixin:
    def get_inherited_permissions(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        return AccessControlList.objects.get_inherited_permissions(
            obj=self.content_object, role=self.role
        )

    def get_permission_count(self):
        return self.permissions.count()
    get_permission_count.short_description = _(message='Permission count')

    def permissions_add(self, queryset, user):
        for obj in queryset:
            self.permissions.add(obj)

        event_acl_edited.commit(
            action_object=self.content_object, actor=user, target=self
        )

    def permissions_remove(self, queryset, user):
        for obj in queryset:
            self.permissions.remove(obj)

        event_acl_edited.commit(
            action_object=self.content_object, actor=user, target=self
        )
