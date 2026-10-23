from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access
from mayan.apps.user_management.permissions import permission_group_edit

from .icons import (
    icon_group_role_list, icon_role_create, icon_role_edit,
    icon_role_group_list, icon_role_list, icon_role_multiple_delete,
    icon_role_permission_list, icon_role_single_delete
)
from .permissions import (
    permission_role_create, permission_role_delete, permission_role_edit,
    permission_role_view
)


link_group_role_list = Link(
    args='object.id', icon=icon_group_role_list,
    permission=permission_group_edit, text=_(message='Roles'),
    view='permissions:group_role_list'
)


link_role_create = Link(
    icon=icon_role_create, permission=permission_role_create,
    text=_(message='Create new role'), view='permissions:role_create'
)
link_role_delete_single = Link(
    args='object.id', icon=icon_role_single_delete,
    permission=permission_role_delete, tags='dangerous',
    text=_(message='Delete'), view='permissions:role_single_delete'
)
link_role_delete_multiple = Link(
    icon=icon_role_multiple_delete, tags='dangerous', text=_(message='Delete'),
    view='permissions:role_multiple_delete'
)
link_role_edit = Link(
    args='object.id', icon=icon_role_edit,
    permission=permission_role_edit, text=_(message='Edit'),
    view='permissions:role_edit'
)
link_role_group_list = Link(
    args='object.id', icon=icon_role_group_list,
    permission=permission_role_edit, text=_(message='Groups'),
    view='permissions:role_group_list'
)
link_role_list = Link(
    icon=icon_role_list, text=_(message='Roles'), view='permissions:role_list'
)
link_role_permission_list = Link(
    args='object.id', icon=icon_role_permission_list,
    permission=permission_role_edit,
    text=_(message='Role permissions'), view='permissions:role_permission_list'
)
link_role_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='permissions', model_name='Role',
        object_permission=permission_role_view,
        view_permission=permission_role_create,
    ), icon=icon_role_list, text=_(message='Roles'),
    view='permissions:role_list'
)
