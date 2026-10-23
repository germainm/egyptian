from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_type_sequence_list, icon_sequence_backend_selection,
    icon_sequence_delete, icon_sequence_document_type_list, icon_sequence_edit,
    icon_sequence_list, icon_sequence_reset, icon_sequence_setup
)
from .permissions import (
    permission_sequence_create, permission_sequence_delete,
    permission_sequence_edit, permission_sequence_reset,
    permission_sequence_view
)

link_document_type_sequence_list = Link(
    args='resolved_object.pk', icon=icon_document_type_sequence_list,
    permission=permission_sequence_view, text=_(message='Sequences'),
    view='sequences:document_type_sequence_list'
)
link_sequence_backend_selection = Link(
    icon=icon_sequence_backend_selection,
    permission=permission_sequence_create,
    text=_(message='Create sequence'),
    view='sequences:sequence_backend_selection'
)
link_sequence_delete = Link(
    args='resolved_object.pk', icon=icon_sequence_delete,
    permission=permission_sequence_delete, tags='dangerous',
    text=_(message='Delete'), view='sequences:sequence_delete'
)
link_sequence_document_type_list = Link(
    args='resolved_object.pk', icon=icon_sequence_document_type_list,
    permission=permission_sequence_edit, text=_(message='Document types'),
    view='sequences:sequence_document_type_list'
)
link_sequence_edit = Link(
    args='resolved_object.pk', icon=icon_sequence_edit,
    permission=permission_sequence_edit, text=_(message='Edit'),
    view='sequences:sequence_edit'
)
link_sequence_list = Link(
    icon=icon_sequence_list, text=_(message='Sequence list'),
    view='sequences:sequence_list'
)
link_sequence_reset = Link(
    args='resolved_object.pk', icon=icon_sequence_reset,
    permission=permission_sequence_reset, tags='dangerous',
    text=_(message='Reset'), view='sequences:sequence_reset'
)
link_sequence_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='sequences', model_name='Sequence',
        object_permission=permission_sequence_view,
        view_permission=permission_sequence_create
    ), icon=icon_sequence_setup, text=_(message='Sequences'),
    view='sequences:sequence_list'
)
