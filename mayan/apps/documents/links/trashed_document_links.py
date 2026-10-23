from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from ..icons import (
    icon_document_trash_multiple, icon_document_trash_single,
    icon_trash_can_empty, icon_trashed_document_delete_multiple,
    icon_trashed_document_delete_single, icon_trashed_document_list,
    icon_trashed_document_restore_multiple,
    icon_trashed_document_restore_single
)
from ..permissions import (
    permission_document_trash, permission_trash_empty,
    permission_trashed_document_delete, permission_trashed_document_restore
)


link_document_trash_multiple = Link(
    icon=icon_document_trash_multiple, tags='dangerous',
    text=_(message='Move to trash'), view='documents:document_multiple_trash'
)
link_document_trash_single = Link(
    args='resolved_object.id', icon=icon_document_trash_single,
    permission=permission_document_trash, tags='dangerous',
    text=_(message='Move to trash'), view='documents:document_trash'
)


link_trash_can_empty = Link(
    icon=icon_trash_can_empty, permission=permission_trash_empty,
    text=_(message='Empty trash'), view='documents:trash_can_empty'
)
link_trashed_document_delete_multiple = Link(
    icon=icon_trashed_document_delete_multiple, tags='dangerous',
    text=_(message='Delete'), view='documents:document_multiple_delete'
)
link_trashed_document_delete_single = Link(
    args='resolved_object.id', icon=icon_trashed_document_delete_single,
    permission=permission_trashed_document_delete,
    tags='dangerous', text=_(message='Delete'),
    view='documents:document_delete'
)
link_trashed_document_list = Link(
    icon=icon_trashed_document_list, text=_(message='Trash can'),
    view='documents:document_list_deleted'
)
link_trashed_document_restore_multiple = Link(
    icon=icon_trashed_document_restore_multiple, text=_(message='Restore'),
    view='documents:document_multiple_restore'
)
link_trashed_document_restore_single = Link(
    args='object.pk', icon=icon_trashed_document_restore_single,
    permission=permission_trashed_document_restore, text=_(message='Restore'),
    view='documents:document_restore'
)
