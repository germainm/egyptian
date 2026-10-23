import copy

from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.links import link_acl_list
from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_cabinet_child_add, icon_cabinet_create, icon_cabinet_delete,
    icon_cabinet_edit, icon_cabinet_list, icon_cabinet_view,
    icon_document_cabinet_add, icon_document_cabinet_remove,
    icon_document_multiple_cabinet_add
)
from .permissions import (
    permission_cabinet_add_document, permission_cabinet_create,
    permission_cabinet_delete, permission_cabinet_edit,
    permission_cabinet_remove_document, permission_cabinet_view
)


def condition_cabinet_is_root(context, resolved_object):
    return context['resolved_object'].is_root_node()



link_document_cabinet_list = Link(
    args='resolved_object.pk', icon=icon_cabinet_list,
    permission=permission_cabinet_view, text=_(message='Cabinets'),
    view='cabinets:document_cabinet_list'
)
link_document_cabinet_remove = Link(
    args='resolved_object.pk', icon=icon_document_cabinet_remove,
    permission=permission_cabinet_remove_document,
    text=_(message='Remove from cabinets'), view='cabinets:document_cabinet_remove'
)
link_document_cabinet_add = Link(
    args='object.pk', icon=icon_document_cabinet_add,
    permission=permission_cabinet_add_document,
    text=_(message='Add to cabinets'), view='cabinets:document_cabinet_add'
)
link_document_multiple_cabinet_add = Link(
    icon=icon_document_multiple_cabinet_add, text=_(message='Add to cabinets'),
    view='cabinets:document_multiple_cabinet_add'
)
link_multiple_document_cabinet_remove = Link(
    icon=icon_document_cabinet_remove, text=_(message='Remove from cabinets'),
    view='cabinets:multiple_document_cabinet_remove'
)


link_custom_acl_list = copy.copy(link_acl_list)
link_custom_acl_list.condition = condition_cabinet_is_root

link_cabinet_child_add = Link(
    args='object.pk', icon=icon_cabinet_child_add,
    permission=permission_cabinet_create, text=_(message='Add new level'),
    view='cabinets:cabinet_child_add'
)
link_cabinet_create = Link(
    icon=icon_cabinet_create, permission=permission_cabinet_create,
    text=_(message='Create cabinet'), view='cabinets:cabinet_create'
)
link_cabinet_delete = Link(
    args='object.pk', icon=icon_cabinet_delete,
    permission=permission_cabinet_delete, tags='dangerous',
    text=_(message='Delete'), view='cabinets:cabinet_delete'
)
link_cabinet_edit = Link(
    args='object.pk', icon=icon_cabinet_edit,
    permission=permission_cabinet_edit, text=_(message='Edit'),
    view='cabinets:cabinet_edit'
)
link_cabinet_list = Link(
    condition=factory_condition_queryset_access(
        app_label='cabinets', model_name='Cabinet',
        object_permission=permission_cabinet_view,
    ), icon=icon_cabinet_list,
    text=_(message='All'), view='cabinets:cabinet_list'
)
link_cabinet_view = Link(
    args='object.pk', icon=icon_cabinet_view,
    permission=permission_cabinet_view, text=_(message='Details'),
    view='cabinets:cabinet_view'
)
