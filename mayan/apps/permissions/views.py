from django.contrib.auth.models import Group
from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.user_management.permissions import permission_group_edit
from mayan.apps.views.generics import (
    AddRemoveView, MultipleObjectDeleteView, SingleObjectCreateView,
    SingleObjectDetailView, SingleObjectEditView, SingleObjectListView
)

from .forms import StoredPermissionDetailForm
from .icons import (
    icon_group_role_list, icon_permission_detail, icon_role_create,
    icon_role_edit, icon_role_group_list, icon_role_list,
    icon_role_permission_list, icon_role_single_delete
)
from .links import link_role_create
from .models import Role, StoredPermission
from .permissions import (
    permission_role_create, permission_role_delete, permission_role_edit,
    permission_role_view
)


class GroupRoleAddRemoveView(AddRemoveView):
    list_added_title = _(message='Group roles')
    list_available_title = _(message='Available roles')
    main_object_method_add_name = 'roles_add'
    main_object_method_remove_name = 'roles_remove'
    main_object_model = Group
    main_object_permission = permission_group_edit
    main_object_pk_url_kwarg = 'group_id'
    related_field = 'roles'
    secondary_object_model = Role
    secondary_object_permission = permission_role_edit
    view_icon = icon_group_role_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(message='Roles of group: %s') % self.main_object
        }


class RoleCreateView(SingleObjectCreateView):
    fields = ('label',)
    model = Role
    post_action_redirect = reverse_lazy(viewname='permissions:role_list')
    view_icon = icon_role_create
    view_permission = permission_role_create

    def get_extra_context(self):
        return {
            'title': _(message='Create new role')
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class RoleDeleteView(MultipleObjectDeleteView):
    error_message = _(
        message='Error deleting role "%(instance)s"; %(exception)s'
    )
    model = Role
    object_permission = permission_role_delete
    pk_url_kwarg = 'role_id'
    post_action_redirect = reverse_lazy(viewname='permissions:role_list')
    success_message_plural = _(
        message='%(count)d roles deleted successfully.'
    )
    success_message_single = _(
        message='Role "%(object)s" deleted successfully.'
    )
    success_message_singular = _(
        message='%(count)d role deleted successfully.'
    )
    title_single = _(message='Delete role: %(object)s.')
    title_singular = _(message='Delete the %(count)d selected role.')
    title_plural = _(message='Delete the %(count)d selected roles.')
    view_icon = icon_role_single_delete


class RoleEditView(SingleObjectEditView):
    fields = ('label',)
    model = Role
    object_permission = permission_role_edit
    pk_url_kwarg = 'role_id'
    view_icon = icon_role_edit

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class RoleListView(SingleObjectListView):
    model = Role
    object_permission = permission_role_view
    view_icon = icon_role_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_role_list,
            'no_results_main_link': link_role_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Roles are authorization units. They contain '
                'user groups which inherit the role permissions for the '
                'entire system. Roles can also be part of access '
                'control lists. Access control lists are permissions '
                'granted to a role for specific objects which its group '
                'members inherit.'
            ),
            'no_results_title': _(message='There are no roles'),
            'title': _(message='Roles')
        }


class RoleGroupAddRemoveView(AddRemoveView):
    list_added_title = _(message='Role groups')
    list_available_title = _(message='Available groups')
    main_object_method_add_name = 'groups_add'
    main_object_method_remove_name = 'groups_remove'
    main_object_model = Role
    main_object_permission = permission_role_edit
    main_object_pk_url_kwarg = 'role_id'
    secondary_object_model = Group
    secondary_object_permission = permission_group_edit
    related_field = 'groups'
    view_icon = icon_role_group_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'subtitle': _(
                message='Add groups to be part of a role. They will '
                'inherit the role\'s permissions and access controls.'
            ),
            'title': _(message='Groups of role: %s') % self.main_object
        }


class RolePermissionAddRemoveView(AddRemoveView):
    list_added_title = _(message='Granted permissions')
    list_available_title = _(message='Available permissions')
    grouped = True
    main_object_method_add_name = 'permissions_add'
    main_object_method_remove_name = 'permissions_remove'
    main_object_model = Role
    main_object_permission = permission_role_edit
    main_object_pk_url_kwarg = 'role_id'
    related_field = 'permissions'
    secondary_object_model = StoredPermission
    view_icon = icon_role_permission_list

    def generate_choices(self, queryset):
        namespaces_dictionary = {}

        object_list = sorted(
            queryset,
            key=lambda permission: str(permission)
        )

        for permission in object_list:
            namespaces_dictionary.setdefault(
                str(permission.namespace_label), []
            )
            namespaces_dictionary[
                str(permission.namespace_label)
            ].append(
                (
                    permission.pk, str(permission)
                )
            )

        return sorted(
            namespaces_dictionary.items()
        )

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'subtitle': _(
                message='Permissions granted here will apply to the entire system '
                'and all objects.'
            ),
            'title': _(message='Permissions for role: %s') % self.main_object
        }


class StoredPermissionDetailView(SingleObjectDetailView):
    form_class = StoredPermissionDetailForm
    form_extra_kwargs = {
        'extra_fields': [
            {
                'field': 'volatile_permission'
            }
        ]
    }
    model = StoredPermission
    pk_url_kwarg = 'stored_permission_id'
    view_icon = icon_permission_detail

    def get_extra_context(self, **kwargs):
        return {
            'object': self.object,
            'title': _(message='Details of permission: %s') % self.object
        }
