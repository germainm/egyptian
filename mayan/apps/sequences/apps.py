import logging

from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_list_facet, menu_object, menu_related, menu_return, menu_secondary,
    menu_setup
)
from mayan.apps.documents.links.document_type_links import (
    link_document_type_list
)
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import SequenceBackend
from .events import (
    event_sequence_edited, event_sequence_exhausted, event_sequence_reset,
    event_sequence_used
)
from .methods import (
    method_document_type_sequences_add, method_document_type_sequences_remove
)
from .links import (
    link_document_type_sequence_list, link_sequence_backend_selection,
    link_sequence_delete, link_sequence_document_type_list,
    link_sequence_edit, link_sequence_list, link_sequence_reset,
    link_sequence_setup
)
from .permissions import (
    permission_sequence_delete, permission_sequence_edit,
    permission_sequence_reset, permission_sequence_use,
    permission_sequence_view
)

logger = logging.getLogger(name=__name__)


class SequencesApp(MayanAppConfig):
    app_namespace = 'sequences'
    app_url = 'sequences'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.sequences'
    verbose_name = _(message='Sequences')

    def ready(self):
        super().ready()

        SequenceBackend.load_modules()

        Sequence = self.get_model(model_name='Sequence')

        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )

        DocumentType.add_to_class(
            name='sequences_add', value=method_document_type_sequences_add
        )
        DocumentType.add_to_class(
            name='sequences_remove',
            value=method_document_type_sequences_remove
        )

        EventModelRegistry.register(model=Sequence)

        ModelEventType.register(
            model=Sequence, event_types=(
                event_sequence_edited, event_sequence_exhausted,
                event_sequence_reset, event_sequence_used
            )
        )

        ModelPermission.register(
            model=Sequence, permissions=(
                permission_sequence_delete, permission_sequence_edit,
                permission_sequence_reset, permission_sequence_use,
                permission_sequence_view
            )
        )

        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=Sequence
        )
        SourceColumn(
            attribute='internal_name', include_label=True, is_sortable=True,
            source=Sequence
        )
        SourceColumn(
            attribute='get_backend_class_label', include_label=True,
            source=Sequence
        )
        SourceColumn(
            attribute='position', include_label=True, is_sortable=True,
            source=Sequence
        )
        SourceColumn(
            attribute='get_value_preview', include_label=True, source=Sequence
        )
        SourceColumn(
            attribute='get_position_remaining_display', include_label=True,
            source=Sequence
        )
        SourceColumn(
            attribute='get_value_is_unique_display', include_label=True,
            source=Sequence
        )


        menu_list_facet.bind_links(
            links=(link_sequence_document_type_list,), sources=(Sequence,)
        )
        menu_object.bind_links(
            links=(
                link_sequence_edit,
                link_sequence_reset, link_sequence_delete
            ), sources=(Sequence,)
        )

        menu_related.bind_links(
            links=(
                link_document_type_list,
            ), sources=(
                Sequence, 'sequences:sequence_list',
                'sequences:sequence_create'
            )
        )
        menu_return.bind_links(
            links=(link_sequence_list,), sources=(
                Sequence, 'sequences:sequence_backend_selection',
                'sequences:sequence_create', 'sequences:sequence_list'
            )
        )
        menu_secondary.bind_links(
            links=(link_sequence_backend_selection,), sources=(
                Sequence, 'sequences:sequence_backend_selection',
                'sequences:sequence_create', 'sequences:sequence_list'
            )
        )
        menu_setup.bind_links(
            links=(link_sequence_setup,)
        )


        menu_list_facet.bind_links(
            links=(link_document_type_sequence_list,), sources=(DocumentType,)
        )
        menu_related.bind_links(
            links=(link_sequence_list,),
            sources=(
                DocumentType, 'documents:document_type_list',
                'documents:document_type_create'
            )
        )
