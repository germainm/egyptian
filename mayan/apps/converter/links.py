from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .classes import LayerLink
from .icons import (
    icon_asset_create, icon_asset_delete_multiple, icon_asset_delete_single,
    icon_asset_edit, icon_asset_list, icon_transformation_delete,
    icon_transformation_edit, icon_transformation_select
)
from .layers import layer_saved_transformations
from .permissions import (
    permission_asset_create, permission_asset_delete, permission_asset_edit,
    permission_asset_view
)
from .transformations import BaseTransformation


def conditional_active(context, resolved_link):
    return resolved_link.link.view == resolved_link.current_view_name and context['layer'] == resolved_link.link.get_layer(context=context)


def condition_valid_transformation_and_arguments(context, resolved_object):
    try:
        transformation = BaseTransformation.get(name=resolved_object.name)
    except KeyError:
        return False
    else:
        return transformation.arguments


link_asset_create = Link(
    icon=icon_asset_create, permission=permission_asset_create,
    text=_(message='Create asset'), view='converter:asset_create'
)
link_asset_delete_multiple = Link(
    icon=icon_asset_delete_multiple, tags='dangerous', text=_(message='Delete'),
    view='converter:asset_multiple_delete'
)
link_asset_delete_single = Link(
    args='object.pk', icon=icon_asset_delete_single,
    permission=permission_asset_delete, tags='dangerous',
    text=_(message='Delete'), view='converter:asset_single_delete'
)
link_asset_edit = Link(
    args='object.pk', icon=icon_asset_edit,
    permission=permission_asset_edit, text=_(message='Edit'),
    view='converter:asset_edit'
)
link_asset_list = Link(
    icon=icon_asset_list, text=_(message='Assets'),
    view='converter:asset_list'
)
link_asset_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='converter', model_name='Asset',
        object_permission=permission_asset_view,
        view_permission=permission_asset_create,
    ), icon=icon_asset_list, text=_(message='Assets'),
    view='converter:asset_list'
)


link_transformation_delete_multiple = LayerLink(
    action='delete', icon=icon_transformation_delete, multi_item=True,
    tags='dangerous', text=_(message='Delete'),
    view='converter:transformation_delete_multiple'
)
link_transformation_delete_single = LayerLink(
    action='delete', icon=icon_transformation_delete, tags='dangerous',
    text=_(message='Delete'), view='converter:transformation_delete_single'
)
link_transformation_edit = LayerLink(
    action='edit', condition=condition_valid_transformation_and_arguments,
    icon=icon_transformation_edit, text=_(message='Edit'),
    view='converter:transformation_edit'
)
link_transformation_list = LayerLink(
    action='view', conditional_active=conditional_active,
    layer=layer_saved_transformations, text=_(message='Transformations'),
    view='converter:transformation_list'
)
link_transformation_select = LayerLink(
    action='select', icon=icon_transformation_select,
    text=_(message='Select new transformation'),
    view='converter:transformation_select'
)
