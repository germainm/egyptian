from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from ..icons import (
    icon_document_list, icon_document_preview,
    icon_document_properties_detail, icon_document_properties_edit,
    icon_document_recently_accessed_list, icon_document_recently_created_list,
    icon_document_type_change_multiple, icon_document_type_change_single
)
from ..permissions import (
    permission_document_properties_edit, permission_document_view
)

link_document_list = Link(
    icon=icon_document_list,
    text=_(message='All documents'), view='documents:document_list'
)
link_document_preview = Link(
    args='resolved_object.id', icon=icon_document_preview,
    permission=permission_document_view, text=_(message='Preview'),
    view='documents:document_preview'
)
link_document_properties_detail = Link(
    args='resolved_object.id', icon=icon_document_properties_detail,
    permission=permission_document_view, text=_(message='Properties'),
    view='documents:document_properties'
)
link_document_properties_edit = Link(
    args='resolved_object.id',
    icon=icon_document_properties_edit,
    permission=permission_document_properties_edit,
    text=_(message='Edit properties'),
    view='documents:document_properties_edit'
)


link_document_type_change_multiple = Link(
    text=_(message='Change type'), icon=icon_document_type_change_multiple,
    view='documents:document_multiple_type_change'
)
link_document_type_change_single = Link(
    args='resolved_object.id', icon=icon_document_type_change_single,
    permission=permission_document_properties_edit, text=_(
        message='Change type'
    ), view='documents:document_type_change'
)


link_document_recently_accessed_list = Link(
    icon=icon_document_recently_accessed_list, text=_(
        message='Recently accessed'
    ), view='documents:document_recently_accessed_list'
)


link_document_recently_created_list = Link(
    icon=icon_document_recently_created_list, text=_(
        message='Recently created'
    ), view='documents:document_recently_created_list'
)
