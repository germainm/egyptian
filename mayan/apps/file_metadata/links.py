from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import (
    icon_document_file_metadata_submit_multiple,
    icon_document_file_metadata_submit_single,
    icon_document_type_file_metadata_driver_configuration_edit,
    icon_document_type_file_metadata_driver_configuration_list,
    icon_document_type_file_metadata_submit, icon_file_metadata,
    icon_file_metadata_driver_list
)
from .permissions import (
    permission_document_type_file_metadata_setup,
    permission_file_metadata_submit, permission_file_metadata_view
)


link_document_file_metadata_driver_list = Link(
    icon=icon_file_metadata,
    kwargs={'document_file_id': 'resolved_object.id'},
    permission=permission_file_metadata_view, text=_(message='File metadata'),
    view='file_metadata:document_file_metadata_driver_list'
)
link_document_file_metadata_driver_attribute_list = Link(
    icon=icon_file_metadata,
    kwargs={'document_file_driver_id': 'resolved_object.id'},
    permission=permission_file_metadata_view, text=_(message='Attributes'),
    view='file_metadata:document_file_metadata_driver_attribute_list'
)
link_document_file_metadata_submit_multiple = Link(
    icon=icon_document_file_metadata_submit_multiple,
    text=_(message='Submit for file metadata'),
    view='file_metadata:document_file_metadata_multiple_submit'
)
link_document_file_metadata_submit_single = Link(
    icon=icon_document_file_metadata_submit_single,
    kwargs={'document_file_id': 'resolved_object.id'},
    permission=permission_file_metadata_submit,
    text=_(message='Submit for file metadata'),
    view='file_metadata:document_file_metadata_single_submit'
)


link_document_type_file_metadata_driver_configuration_edit = Link(
    icon=icon_document_type_file_metadata_driver_configuration_edit,
    kwargs={
        'document_type_id': 'document_type.id',
        'stored_driver_id': 'resolved_object.stored_driver_id'
    }, permission=permission_document_type_file_metadata_setup,
    text=_(message='Edit'),
    view='file_metadata:document_type_file_metadata_driver_configuration_edit'
)
link_document_type_file_metadata_driver_configuration_list = Link(
    icon=icon_document_type_file_metadata_driver_configuration_list,
    kwargs={'document_type_id': 'resolved_object.id'},
    permission=permission_document_type_file_metadata_setup,
    text=_(message='File metadata driver setup'),
    view='file_metadata:document_type_file_metadata_driver_configuration_list'
)
link_document_type_file_metadata_submit = Link(
    icon=icon_document_type_file_metadata_submit,
    permission=permission_file_metadata_submit,
    text=_(message='File metadata processing per type'),
    view='file_metadata:document_type_file_metadata_submit'
)


link_file_metadata_driver_list = Link(
    icon=icon_file_metadata_driver_list,
    permission=permission_file_metadata_view,
    text=_(message='File metadata drivers'),
    view='file_metadata:file_metadata_driver_list'
)
