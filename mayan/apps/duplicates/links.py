from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import (
    permission_document_tools, permission_document_view
)
from mayan.apps.navigation.links import Link

from .icons import (
    icon_document_duplicate_backend_document_list,
    icon_document_duplicate_backend_list, icon_duplicate_backend_document_list,
    icon_duplicate_backend_list, icon_duplicated_document_scan
)


link_document_duplicate_backend_list = Link(
    icon=icon_document_duplicate_backend_list,
    kwargs={'document_id': 'resolved_object.id'},
    permission=permission_document_view, text=_(message='Duplicates'),
    view='duplicates:document_duplicate_backend_list'
)
link_document_duplicate_backend_document_list = Link(
    icon=icon_document_duplicate_backend_document_list,
    kwargs={
        'backend_entry_id': 'resolved_object.id',
        'document_id': 'resolved_object.document_id'
    }, text=_(message='Documents'),
    view='duplicates:document_duplicate_backend_document_list'
)


link_duplicate_backend_list = Link(
    icon=icon_duplicate_backend_list, text=_(message='Duplicates'),
    view='duplicates:duplicate_backend_list'
)
link_duplicate_backend_document_list = Link(
    icon=icon_duplicate_backend_document_list,
    kwargs={'stored_duplicated_backend_id': 'resolved_object.id'},
    text=_(message='Documents'),
    view='duplicates:duplicate_backend_document_list'
)


link_duplicated_document_scan = Link(
    icon=icon_duplicated_document_scan, permission=permission_document_tools,
    text=_(message='Duplicated document scan'),
    view='duplicates:duplicated_document_scan'
)
