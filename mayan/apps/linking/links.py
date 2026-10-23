from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import (
    permission_document_type_edit, permission_document_view
)
from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_smart_link_instance_list, icon_document_type_smart_links,
    icon_smart_link_condition_create, icon_smart_link_condition_delete,
    icon_smart_link_condition_edit, icon_smart_link_condition_list,
    icon_smart_link_create, icon_smart_link_delete,
    icon_smart_link_document_type_list, icon_smart_link_edit,
    icon_smart_link_instance_detail, icon_smart_link_list,
    icon_smart_link_setup
)
from .permissions import (
    permission_smart_link_create, permission_smart_link_delete,
    permission_smart_link_edit, permission_smart_link_view
)


link_document_smart_link_instance_list = Link(
    args='resolved_object.pk',
    icon=icon_document_smart_link_instance_list,
    permission=permission_document_view, text=_(message='Smart links'),
    view='linking:document_smart_link_instance_list'
)


link_document_type_smart_links = Link(
    args='resolved_object.pk', icon=icon_document_type_smart_links,
    permission=permission_document_type_edit, text=_(message='Smart links'),
    view='linking:document_type_smart_links'
)


link_smart_link_create = Link(
    icon=icon_smart_link_create,
    permission=permission_smart_link_create,
    text=_(message='Create new smart link'), view='linking:smart_link_create'
)
link_smart_link_delete = Link(
    args='object.pk', icon=icon_smart_link_delete,
    permission=permission_smart_link_delete, tags='dangerous',
    text=_(message='Delete'), view='linking:smart_link_delete'
)
link_smart_link_document_types = Link(
    args='object.pk', icon=icon_smart_link_document_type_list,
    permission=permission_smart_link_edit, text=_(message='Document types'),
    view='linking:smart_link_document_types'
)
link_smart_link_edit = Link(
    args='object.pk', icon=icon_smart_link_edit,
    permission=permission_smart_link_edit, text=_(message='Edit'),
    view='linking:smart_link_edit'
)
link_smart_link_instance_view = Link(
    args=('document.pk', 'object.pk',), icon=icon_smart_link_instance_detail,
    permission=permission_smart_link_view, text=_(message='Documents'),
    view='linking:smart_link_instance_view'
)
link_smart_link_list = Link(
    icon=icon_smart_link_list, text=_(message='Smart links'),
    view='linking:smart_link_list'
)
link_smart_link_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='linking', model_name='SmartLink',
        object_permission=permission_smart_link_view,
        view_permission=permission_smart_link_create,
    ), icon=icon_smart_link_setup, text=_(message='Smart links'),
    view='linking:smart_link_list'
)


link_smart_link_condition_create = Link(
    args='object.pk', icon=icon_smart_link_condition_create,
    permission=permission_smart_link_edit, text=_(message='Create condition'),
    view='linking:smart_link_condition_create'
)
link_smart_link_condition_delete = Link(
    args='resolved_object.pk', icon=icon_smart_link_condition_delete,
    permission=permission_smart_link_edit, tags='dangerous',
    text=_(message='Delete'), view='linking:smart_link_condition_delete'
)
link_smart_link_condition_edit = Link(
    args='resolved_object.pk', icon=icon_smart_link_condition_edit,
    permission=permission_smart_link_edit, text=_(message='Edit'),
    view='linking:smart_link_condition_edit'
)
link_smart_link_condition_list = Link(
    args='object.pk', icon=icon_smart_link_condition_list,
    permission=permission_smart_link_edit, text=_(message='Conditions'),
    view='linking:smart_link_condition_list'
)
