from django.apps import apps
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_list_facet, menu_multi_item, menu_object, menu_secondary, menu_tools
)
from mayan.apps.databases.classes import ModelFieldRelated, ModelProperty
from mayan.apps.documents.signals import signal_post_document_file_upload
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.forms import column_widgets
from mayan.apps.logging.classes import ErrorLogDomain
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import FileMetadataDriver
from .events import (
    event_file_metadata_document_file_finished,
    event_file_metadata_document_file_submitted
)
from .handlers import (
    handler_initialize_new_document_type_file_metadata_driver_configuration,
    handler_post_document_file_upload
)
from .links import (
    link_document_file_metadata_driver_attribute_list,
    link_document_file_metadata_driver_list,
    link_document_file_metadata_submit_multiple,
    link_document_file_metadata_submit_single,
    link_document_type_file_metadata_driver_configuration_edit,
    link_document_type_file_metadata_driver_configuration_list,
    link_document_type_file_metadata_submit, link_file_metadata_driver_list
)
from .literals import ERROR_LOG_DOMAIN_NAME
from .methods import (
    method_document_file_metadata_submit,
    method_document_file_metadata_submit_single,
    method_get_document_file_file_metadata
)
from .permissions import (
    permission_document_type_file_metadata_setup,
    permission_file_metadata_submit, permission_file_metadata_view
)
from .property_helpers import (
    DocumentFileMetadataHelper, DocumentFileFileMetadataHelper
)


class FileMetadataApp(MayanAppConfig):
    app_namespace = 'file_metadata'
    app_url = 'file_metadata'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.file_metadata'
    verbose_name = _(message='File metadata')

    def ready(self):
        super().ready()

        FileMetadataEntry = self.get_model(model_name='FileMetadataEntry')
        DocumentFileDriverEntry = self.get_model(
            model_name='DocumentFileDriverEntry'
        )
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )
        DocumentTypeDriverConfiguration = self.get_model(
            model_name='DocumentTypeDriverConfiguration'
        )
        StoredDriver = self.get_model(
            model_name='StoredDriver'
        )

        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )
        Document.add_to_class(
            name='file_metadata_value_of',
            value=DocumentFileMetadataHelper.constructor
        )
        Document.add_to_class(
            name='submit_for_file_metadata_processing',
            value=method_document_file_metadata_submit
        )

        DocumentFile.add_to_class(
            name='file_metadata_value_of',
            value=DocumentFileFileMetadataHelper.constructor
        )
        DocumentFile.add_to_class(
            name='get_file_metadata',
            value=method_get_document_file_file_metadata
        )
        DocumentFile.add_to_class(
            name='submit_for_file_metadata_processing',
            value=method_document_file_metadata_submit_single
        )

        EventModelRegistry.register(model=StoredDriver)

        ErrorLogDomain(
            label=_(message='File metadata'), name=ERROR_LOG_DOMAIN_NAME
        )

        FileMetadataDriver.load_modules()
        FileMetadataDriver.initialize()

        ModelEventType.register(
            model=Document, event_types=(
                event_file_metadata_document_file_finished,
                event_file_metadata_document_file_submitted
            )
        )

        ModelFieldRelated(
            model=Document,
            name='files__file_metadata_drivers__entries__internal_name'
        )
        ModelFieldRelated(
            model=Document,
            name='files__file_metadata_drivers__entries__value'
        )

        ModelPermission.register(
            model=Document, permissions=(
                permission_file_metadata_submit,
                permission_file_metadata_view
            )
        )
        ModelPermission.register(
            model=DocumentType, permissions=(
                permission_document_type_file_metadata_setup,
                permission_file_metadata_submit,
                permission_file_metadata_view
            )
        )
        ModelPermission.register_inheritance(
            model=DocumentFileDriverEntry, related='document_file'
        )
        ModelPermission.register_inheritance(
            model=DocumentTypeDriverConfiguration, related='document_type'
        )

        ModelProperty(
            description=_(
                message='Return the value of a specific file metadata.'
            ), label=_(message='File metadata value of'), model=Document,
            name='file_metadata_value_of.< underscore separated driver name and property name >'
        )
        ModelProperty(
            description=_(
                message='Return the value of a specific file metadata.'
            ), label=_(message='File metadata value of'), model=DocumentFile,
            name='file_metadata_value_of.< underscore separated driver name and property name >'
        )


        SourceColumn(
            attribute='internal_name', is_identifier=True, is_sortable=True,
            source=FileMetadataEntry
        )
        SourceColumn(
            attribute='key', is_sortable=True, source=FileMetadataEntry
        )
        SourceColumn(
            attribute='get_full_path', source=FileMetadataEntry
        )
        SourceColumn(
            attribute='value', include_label=True, is_sortable=True,
            source=FileMetadataEntry
        )


        SourceColumn(
            attribute='label', include_label=True, label=_(message='Label'),
            source=FileMetadataDriver
        )
        SourceColumn(
            attribute='get_mime_type_list_display', include_label=True,
            label=_(message='MIME types'), source=FileMetadataDriver
        )
        SourceColumn(
            attribute='internal_name', include_label=True,
            label=_(message='Internal name'), source=FileMetadataDriver
        )
        SourceColumn(
            attribute='description', include_label=True,
            label=_(message='Description'), source=FileMetadataDriver
        )
        SourceColumn(
            attribute='get_argument_values_from_settings_display',
            include_label=True, label=_(message='Arguments'),
            source=FileMetadataDriver
        )
        SourceColumn(
            attribute='get_enabled_value',
            help_text=_(
                'Whether or not this driver will be enabled by default for '
                'new document types.'
            ),
            include_label=True, label=_(message='Enabled by default?'),
            source=FileMetadataDriver, widget=column_widgets.TwoStateWidget
        )


        SourceColumn(
            attribute='driver', is_identifier=True,
            source=DocumentFileDriverEntry
        )
        SourceColumn(
            attribute='driver__internal_name', include_label=True,
            is_sortable=True, source=DocumentFileDriverEntry
        )
        SourceColumn(
            attribute='get_attribute_count', include_label=True,
            source=DocumentFileDriverEntry
        )


        SourceColumn(
            attribute='stored_driver', is_identifier=True,
            source=DocumentTypeDriverConfiguration
        )
        SourceColumn(
            attribute='enabled', include_label=True, is_sortable=True,
            source=DocumentTypeDriverConfiguration,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_arguments_display', include_label=True,
            source=DocumentTypeDriverConfiguration
        )

        menu_tools.bind_links(
            links=(
                link_document_type_file_metadata_submit,
                link_file_metadata_driver_list
            )
        )


        menu_list_facet.bind_links(
            links=(link_document_file_metadata_driver_list,),
            sources=(DocumentFile,)
        )

        menu_multi_item.bind_links(
            links=(link_document_file_metadata_submit_multiple,),
            sources=(DocumentFile,)
        )

        menu_secondary.bind_links(
            links=(link_document_file_metadata_submit_single,), sources=(
                'file_metadata:document_file_metadata_driver_list',
                'file_metadata:document_file_metadata_driver_attribute_list'
            )
        )


        menu_object.bind_links(
            links=(link_document_file_metadata_driver_attribute_list,),
            sources=(DocumentFileDriverEntry,)
        )

        menu_object.bind_links(
            links=(
                link_document_type_file_metadata_driver_configuration_edit,
            ), sources=(DocumentTypeDriverConfiguration,)
        )


        menu_list_facet.bind_links(
            links=(
                link_document_type_file_metadata_driver_configuration_list,
            ), sources=(DocumentType,)
        )

        post_save.connect(
            dispatch_uid='file_metadata_handler_initialize_new_document_type_file_metadata_driver_configuration',
            receiver=handler_initialize_new_document_type_file_metadata_driver_configuration,
            sender=DocumentType
        )
        signal_post_document_file_upload.connect(
            dispatch_uid='file_metadata_handler_post_document_file_upload',
            receiver=handler_post_document_file_upload,
            sender=DocumentFile
        )
