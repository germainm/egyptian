from django.apps import apps
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.classes import ModelCopy
from mayan.apps.common.menus import (
    menu_list_facet, menu_main, menu_object, menu_related, menu_return,
    menu_secondary, menu_setup, menu_tools
)
from mayan.apps.documents.links.document_type_links import (
    link_document_type_list
)
from mayan.apps.documents.signals import signal_post_initial_document_type
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.rest_api.fields import DynamicSerializerField

from .events import event_index_template_created, event_index_template_edited
from .handlers import (
    handler_create_default_document_index, handler_event_trigger,
    handler_index_document, handler_remove_document
)
from .column_widgets import (
    IndexInstanceItemLinkWidget, IndexInstanceNodeLinkWidget,
    IndexTemplateNodeLevelWidget
)
from .links import (
    link_document_index_instance_list, link_document_type_index_templates,
    link_index_instance_menu, link_index_instance_rebuild,
    link_index_instances_rebuild, link_index_instances_reset,
    link_index_template_create, link_index_template_delete,
    link_index_template_document_types, link_index_template_edit,
    link_index_template_event_triggers, link_index_template_list,
    link_index_template_node_create, link_index_template_node_delete,
    link_index_template_node_edit, link_index_template_node_tree_view,
    link_index_template_setup
)
from .methods import (
    method_document_type_index_template_add,
    method_document_type_index_template_remove
)
from .permissions import (
    permission_index_instance_view, permission_index_template_delete,
    permission_index_template_edit, permission_index_template_rebuild,
    permission_index_template_view
)


class DocumentIndexingApp(MayanAppConfig):
    app_namespace = 'indexing'
    app_url = 'indexing'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.document_indexing'
    verbose_name = _(message='Document indexing')

    def ready(self):
        super().ready()

        Action = apps.get_model(app_label='actstream', model_name='Action')

        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )

        DocumentIndexInstanceNode = self.get_model(
            model_name='DocumentIndexInstanceNode'
        )

        IndexInstance = self.get_model(model_name='IndexInstance')
        IndexInstanceNode = self.get_model(model_name='IndexInstanceNode')
        IndexInstanceNodeSearchResult = self.get_model(
            model_name='IndexInstanceNodeSearchResult'
        )
        IndexTemplate = self.get_model(model_name='IndexTemplate')
        IndexTemplateNode = self.get_model(model_name='IndexTemplateNode')

        DocumentType.add_to_class(
            name='index_template_add',
            value=method_document_type_index_template_add
        )
        DocumentType.add_to_class(
            name='index_template_remove',
            value=method_document_type_index_template_remove
        )

        DynamicSerializerField.add_serializer(
            klass=IndexTemplate,
            serializer_class='mayan.apps.document_indexing.serializers.index_template_serializers.IndexTemplateSerializer'
        )

        EventModelRegistry.register(model=IndexTemplate)

        ModelCopy(
            excludes={'parent__isnull': False},
            extra_kwargs={'get_or_create': True},
            model=IndexTemplateNode
        ).add_fields(
            field_names=(
                'index', 'expression', 'enabled', 'link_documents'
            )
        )
        ModelCopy(
            model=IndexTemplate, bind_link=True, register_permission=True
        ).add_fields(
            field_names=(
                'label', 'slug', 'enabled', 'document_types',
                'index_template_nodes'
            )
        )

        ModelEventType.register(
            event_types=(
                event_index_template_created, event_index_template_edited
            ), model=IndexTemplate
        )

        ModelPermission.register(
            model=Document, permissions=(
                permission_index_instance_view,
            )
        )
        ModelPermission.register(
            model=IndexTemplate, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_index_template_delete,
                permission_index_template_edit,
                permission_index_instance_view,
                permission_index_template_rebuild,
                permission_index_template_view
            )
        )
        ModelPermission.register_inheritance(
            model=IndexTemplateNode, related='index'
        )

        ModelPermission.register_inheritance(
            model=IndexInstanceNode, related='index_template_node__index'
        )


        SourceColumn(
            include_label=True, is_sortable=True, label=_(message='Level'),
            sort_field='value', source=DocumentIndexInstanceNode,
            widget=IndexInstanceNodeLinkWidget
        )


        SourceColumn(
            attribute='get_level_count', include_label=True,
            label=_(message='Depth'), source=IndexInstance
        )
        SourceColumn(
            attribute='get_descendants_count', include_label=True,
            label=_(message='Total nodes'), source=IndexInstance
        )
        SourceColumn(
            func=lambda context: context[
                'object'
            ].get_descendants_document_count(
                user=context['request'].user
            ), include_label=True, label=_(message='Total documents'),
            help_text=_(
                message='Number of unique documents this item contains.'
            ), source=IndexInstance
        )


        column_index_instance_node_level = SourceColumn(
            is_identifier=True, is_sortable=True, label=_(message='Level'),
            sort_field='value', source=IndexInstanceNode,
            widget=IndexInstanceItemLinkWidget
        )
        column_index_instance_node_level.add_exclude(
            source=DocumentIndexInstanceNode
        )

        column_index_instance_node_level_count = SourceColumn(
            attribute='get_level_count', include_label=True,
            label=_(message='Depth'), source=IndexInstanceNode
        )
        column_index_instance_node_level_count.add_exclude(
            source=DocumentIndexInstanceNode
        )

        column_index_instance_node_count = SourceColumn(
            attribute='get_descendants_count',
            include_label=True, label=_(message='Nodes'), source=IndexInstanceNode
        )
        column_index_instance_node_count.add_exclude(
            source=DocumentIndexInstanceNode
        )

        column_index_instance_node_document_count = SourceColumn(
            func=lambda context: context[
                'object'
            ].get_descendants_document_count(
                user=context['request'].user
            ), include_label=True, label=_(message='Documents'),
            help_text=_(
                message='Number of unique documents this item contains.'
            ), source=IndexInstanceNode
        )
        column_index_instance_node_document_count.add_exclude(
            source=DocumentIndexInstanceNode
        )

        SourceColumn(
            is_identifier=True, is_sortable=True, label=_(message='Level'),
            sort_field='value', source=IndexInstanceNodeSearchResult,
            widget=IndexInstanceItemLinkWidget
        )
        SourceColumn(
            attribute='get_full_path', source=IndexInstanceNodeSearchResult
        )


        column_index_label = SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=IndexTemplate
        )
        column_index_label.add_exclude(source=IndexInstance)
        SourceColumn(
            attribute='label', is_object_absolute_url=True,
            is_identifier=True, is_sortable=True, source=IndexInstance
        )
        column_index_slug = SourceColumn(
            attribute='slug', include_label=True, is_sortable=True,
            source=IndexTemplate
        )
        column_index_slug.add_exclude(source=IndexInstance)
        column_index_enabled = SourceColumn(
            attribute='enabled', include_label=True, is_sortable=True,
            source=IndexTemplate, widget=column_widgets.TwoStateWidget
        )
        column_index_enabled.add_exclude(source=IndexInstance)


        SourceColumn(
            include_label=True, is_identifier=True, label=_(message='Level'),
            source=IndexTemplateNode, widget=IndexTemplateNodeLevelWidget
        )
        SourceColumn(
            attribute='enabled', include_label=True, is_sortable=True,
            source=IndexTemplateNode, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='link_documents', include_label=True, is_sortable=True,
            source=IndexTemplateNode, widget=column_widgets.TwoStateWidget
        )

        menu_list_facet.bind_links(
            links=(
                link_document_index_instance_list,
            ), sources=(Document,)
        )
        menu_list_facet.bind_links(
            links=(link_document_type_index_templates,),
            sources=(DocumentType,)
        )
        menu_list_facet.bind_links(
            links=(
                link_index_template_document_types,
                link_index_template_event_triggers,
                link_index_template_node_tree_view
            ), sources=(IndexTemplate,)
        )
        menu_object.bind_links(
            links=(
                link_index_template_delete, link_index_template_edit,
                link_index_instance_rebuild
            ), sources=(IndexTemplate,)
        )
        menu_object.bind_links(
            links=(
                link_index_template_node_create,
                link_index_template_node_delete,
                link_index_template_node_edit
            ), sources=(IndexTemplateNode,)
        )
        menu_main.bind_links(
            links=(link_index_instance_menu,), position=50
        )
        menu_related.bind_links(
            links=(link_index_template_list,),
            sources=(
                DocumentType, 'documents:document_type_list',
                'documents:document_type_create'
            )
        )
        menu_related.bind_links(
            links=(link_document_type_list,),
            sources=(
                IndexTemplate, 'indexing:index_template_list',
                'indexing:index_template_create'
            )
        )
        menu_return.bind_links(
            links=(link_index_template_list,),
            sources=(
                IndexTemplate, 'indexing:index_template_list',
                'indexing:index_template_create'
            )
        )
        menu_secondary.bind_links(
            links=(link_index_template_create,),
            sources=(
                IndexTemplate, 'indexing:index_template_list',
                'indexing:index_template_create'
            )
        )
        menu_setup.bind_links(
            links=(link_index_template_setup,)
        )
        menu_tools.bind_links(
            links=(link_index_instances_rebuild, link_index_instances_reset)
        )

        post_save.connect(
            dispatch_uid='document_handler_index_document',
            receiver=handler_index_document,
            sender=Document
        )
        post_save.connect(
            dispatch_uid='document_indexing_handler_event_trigger',
            receiver=handler_event_trigger,
            sender=Action
        )
        pre_delete.connect(
            dispatch_uid='document_indexing_handler_remove_document',
            receiver=handler_remove_document,
            sender=Document
        )
        signal_post_initial_document_type.connect(
            dispatch_uid='document_indexing_handler_create_default_document_index',
            receiver=handler_create_default_document_index,
            sender=DocumentType
        )
