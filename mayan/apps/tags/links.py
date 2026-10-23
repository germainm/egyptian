from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_tag_list, icon_document_tag_multiple_attach,
    icon_document_tag_multiple_remove, icon_tag_create,
    icon_tag_delete_multiple, icon_tag_delete_single,
    icon_tag_document_list, icon_tag_edit, icon_tag_list
)
from .permissions import (
    permission_tag_attach, permission_tag_create, permission_tag_delete,
    permission_tag_edit, permission_tag_remove, permission_tag_view
)

link_document_multiple_tag_multiple_attach = Link(
    icon=icon_document_tag_multiple_attach, text=_(message='Attach tags'),
    view='tags:multiple_documents_tag_attach'
)
link_document_multiple_tag_multiple_remove = Link(
    icon=icon_document_tag_multiple_remove, text=_(message='Remove tag'),
    view='tags:multiple_documents_selection_tag_remove'
)
link_document_tag_list = Link(
    args='resolved_object.pk', icon=icon_document_tag_list,
    permission=permission_tag_view, text=_(message='Tags'),
    view='tags:document_tag_list'
)
link_document_tag_multiple_remove = Link(
    args='object.id', icon=icon_document_tag_multiple_remove,
    permission=permission_tag_remove, text=_(message='Remove tags'),
    view='tags:single_document_multiple_tag_remove'
)
link_document_tag_multiple_attach = Link(
    args='object.pk', icon=icon_document_tag_multiple_attach,
    permission=permission_tag_attach, text=_(message='Attach tags'),
    view='tags:tag_attach'
)

link_tag_create = Link(
    icon=icon_tag_create, permission=permission_tag_create,
    text=_(message='Create new tag'), view='tags:tag_create'
)
link_tag_delete_multiple = Link(
    icon=icon_tag_delete_multiple, tags='dangerous',
    text=_(message='Delete'), view='tags:tag_multiple_delete'
)
link_tag_delete_single = Link(
    args='object.id', icon=icon_tag_delete_single,
    permission=permission_tag_delete, tags='dangerous',
    text=_(message='Delete'), view='tags:tag_single_delete'
)
link_tag_edit = Link(
    args='object.id', icon=icon_tag_edit,
    permission=permission_tag_edit, text=_(message='Edit'),
    view='tags:tag_edit'
)
link_tag_list = Link(
    condition=factory_condition_queryset_access(
        app_label='tags', model_name='Tag',
        object_permission=permission_tag_view,
    ), icon=icon_tag_list,
    text=_(message='All'), view='tags:tag_list'
)
link_tag_document_list = Link(
    args='object.id', icon=icon_tag_document_list,
    text=_(message='Documents'), view='tags:tag_document_list'
)
