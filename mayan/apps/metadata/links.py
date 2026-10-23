from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_metadata_add, icon_document_metadata_edit,
    icon_document_metadata_list, icon_document_metadata_remove,
    icon_document_type_metadata_type_list, icon_metadata_type_create,
    icon_metadata_type_delete_multiple, icon_metadata_type_delete_single,
    icon_metadata_type_document_type_list, icon_metadata_type_edit,
    icon_metadata_type_list
)
from .permissions import (
    permission_document_metadata_add, permission_document_metadata_edit,
    permission_document_metadata_remove, permission_document_metadata_view,
    permission_metadata_type_create, permission_metadata_type_delete,
    permission_metadata_type_edit, permission_metadata_type_view
)


link_metadata_add = Link(
    args='object.pk', icon=icon_document_metadata_add,
    permission=permission_document_metadata_add, text=_(message='Add metadata'),
    view='metadata:metadata_add',
)
link_metadata_edit = Link(
    args='object.pk', icon=icon_document_metadata_edit,
    permission=permission_document_metadata_edit,
    text=_(message='Edit metadata'), view='metadata:metadata_edit'
)
link_metadata_multiple_add = Link(
    icon=icon_document_metadata_add, text=_(message='Add metadata'),
    view='metadata:metadata_multiple_add'
)
link_metadata_multiple_edit = Link(
    icon=icon_document_metadata_edit, text=_(message='Edit metadata'),
    view='metadata:metadata_multiple_edit'
)
link_metadata_multiple_remove = Link(
    icon=icon_document_metadata_remove, text=_(message='Remove metadata'),
    view='metadata:metadata_multiple_remove'
)
link_metadata_remove = Link(
    args='object.pk', icon=icon_document_metadata_remove,
    permission=permission_document_metadata_remove,
    text=_(message='Remove metadata'), view='metadata:metadata_remove',
)
link_metadata_list = Link(
    args='resolved_object.pk', icon=icon_document_metadata_list,
    permission=permission_document_metadata_view, text=_(message='Metadata'),
    view='metadata:metadata_list',
)


link_document_type_metadata_type_relationship = Link(
    args='resolved_object.pk',
    icon=icon_document_type_metadata_type_list,
    permission=permission_document_type_edit,
    text=_(message='Metadata types'), view='metadata:document_type_metadata_type_relationship',
)


link_metadata_type_document_type_relationship = Link(
    args='resolved_object.pk',
    icon=icon_metadata_type_document_type_list,
    permission=permission_document_type_edit,
    text=_(message='Document types'), view='metadata:metadata_type_document_type_relationship',
)
link_metadata_type_create = Link(
    icon=icon_metadata_type_create,
    permission=permission_metadata_type_create, text=_(message='Create new'),
    view='metadata:metadata_type_create'
)
link_metadata_type_delete_multiple = Link(
    icon=icon_metadata_type_delete_multiple, tags='dangerous',
    text=_(message='Delete'), view='metadata:metadata_type_multiple_delete'
)
link_metadata_type_delete_single = Link(
    args='object.pk', icon=icon_metadata_type_delete_single,
    permission=permission_metadata_type_delete,
    tags='dangerous', text=_(message='Delete'),
    view='metadata:metadata_type_single_delete',
)
link_metadata_type_edit = Link(
    args='object.pk', icon=icon_metadata_type_edit,
    permission=permission_metadata_type_edit,
    text=_(message='Edit'), view='metadata:metadata_type_edit'
)
link_metadata_type_list = Link(
    icon=icon_metadata_type_list, text=_(message='Metadata types'),
    view='metadata:metadata_type_list'
)
link_metadata_type_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='metadata', model_name='MetadataType',
        object_permission=permission_metadata_type_view,
        view_permission=permission_metadata_type_create,
    ), icon=icon_metadata_type_list, text=_(message='Metadata types'),
    view='metadata:metadata_type_list'
)
