from django.apps import apps
from django.db.models.signals import post_migrate, post_save, pre_delete
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.classes import ModelCopy
from mayan.apps.common.menus import (
    menu_list_facet, menu_main, menu_multi_item, menu_object, menu_related,
    menu_return, menu_secondary, menu_setup, menu_tools
)
from mayan.apps.databases.classes import (
    ModelField, ModelProperty, ModelReverseField
)
from mayan.apps.documents.links.document_type_links import (
    link_document_type_list
)
from mayan.apps.documents.signals import signal_post_document_type_change
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.forms import column_widgets
from mayan.apps.logging.classes import ErrorLog, ErrorLogDomain
from mayan.apps.logging.permissions import permission_error_log_entry_view
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.rest_api.fields import DynamicSerializerField
from mayan.apps.templating.classes import ModelTemplating

from .classes import DocumentStateHelper, WorkflowAction
from .column_widgets import (
    WorkflowLogExtraDataWidget, WorkflowTemplateTransitionTriggerColumnWidget
)
from .events import (
    event_workflow_instance_created, event_workflow_instance_transitioned,
    event_workflow_template_edited
)
from .handlers import (
    handler_create_workflow_image_cache, handler_launch_workflow_on_create,
    handler_launch_workflow_on_type_change, handler_transition_trigger,
    handler_workflow_template_post_edit,
    handler_workflow_template_state_post_edit,
    handler_workflow_template_state_pre_delete,
    handler_workflow_template_transition_post_edit,
    handler_workflow_template_transition_pre_delete
)
from .links import (
    link_document_workflow_templates_launch_multiple,
    link_document_workflow_templates_launch_single,
    link_document_type_workflow_template_list, link_tool_launch_workflows,
    link_workflow_instance_delete_single, link_workflow_instance_detail,
    link_workflow_instance_list, link_workflow_instance_transition,
    link_workflow_runtime_proxy_document_list,
    link_workflow_runtime_proxy_list,
    link_workflow_runtime_proxy_state_document_list,
    link_workflow_runtime_proxy_state_list, link_workflow_template_create,
    link_workflow_template_document_type_list, link_workflow_template_edit,
    link_workflow_template_delete_multiple, link_workflow_template_launch,
    link_workflow_template_list, link_workflow_template_delete_single,
    link_workflow_template_preview, link_workflow_template_setup,
    link_workflow_template_state_list,
    link_workflow_template_state_action_delete,
    link_workflow_template_state_action_edit,
    link_workflow_template_state_action_list,
    link_workflow_template_state_action_selection,
    link_workflow_template_state_create, link_workflow_template_state_delete,
    link_workflow_template_state_edit,
    link_workflow_template_state_escalation_create,
    link_workflow_template_state_escalation_delete,
    link_workflow_template_state_escalation_edit,
    link_workflow_template_state_escalation_list,
    link_workflow_template_transition_create,
    link_workflow_template_transition_delete,
    link_workflow_template_transition_edit,
    link_workflow_template_transition_list,
    link_workflow_template_transition_triggers,
    link_workflow_template_transition_field_create,
    link_workflow_template_transition_field_delete,
    link_workflow_template_transition_field_edit,
    link_workflow_template_transition_field_list
)
from .literals import ERROR_LOG_DOMAIN_NAME
from .methods import (
    method_document_type_workflow_templates_add,
    method_document_type_workflow_templates_remove
)
from .permissions import (
    permission_workflow_template_delete, permission_workflow_template_edit,
    permission_workflow_tools, permission_workflow_instance_delete,
    permission_workflow_instance_transition,
    permission_workflow_template_view
)


class DocumentStatesApp(MayanAppConfig):
    app_namespace = 'document_states'
    app_url = 'workflows'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.document_states'
    verbose_name = _(message='Workflows')

    def ready(self):
        super().ready()

        Action = apps.get_model(
            app_label='actstream', model_name='Action'
        )
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )

        Workflow = self.get_model(model_name='Workflow')
        WorkflowInstance = self.get_model(model_name='WorkflowInstance')
        WorkflowInstanceLogEntry = self.get_model(
            model_name='WorkflowInstanceLogEntry'
        )
        WorkflowRuntimeProxy = self.get_model(
            model_name='WorkflowRuntimeProxy'
        )
        WorkflowState = self.get_model(model_name='WorkflowState')
        WorkflowStateAction = self.get_model(model_name='WorkflowStateAction')
        WorkflowStateEscalation = self.get_model(
            model_name='WorkflowStateEscalation'
        )
        WorkflowStateRuntimeProxy = self.get_model(
            'WorkflowStateRuntimeProxy'
        )
        WorkflowTransition = self.get_model(model_name='WorkflowTransition')
        WorkflowTransitionField = self.get_model(
            model_name='WorkflowTransitionField'
        )
        WorkflowTransitionTriggerEvent = self.get_model(
            'WorkflowTransitionTriggerEvent'
        )

        Document.add_to_class(
            name='workflow', value=DocumentStateHelper.constructor
        )

        DocumentType.add_to_class(
            name='workflow_templates_add',
            value=method_document_type_workflow_templates_add
        )
        DocumentType.add_to_class(
            name='workflow_templates_remove',
            value=method_document_type_workflow_templates_remove
        )

        DynamicSerializerField.add_serializer(
            klass=Workflow,
            serializer_class='mayan.apps.document_states.serializers.workflow_template_serializers.WorkflowTemplateSerializer'
        )

        error_log = ErrorLog(app_config=self)
        error_log.register_model(model=WorkflowStateAction)

        ErrorLogDomain(
            label=_(message='Workflows'), name=ERROR_LOG_DOMAIN_NAME
        )

        EventModelRegistry.register(model=WorkflowInstance)
        EventModelRegistry.register(
            exclude=(WorkflowRuntimeProxy,), model=Workflow,
        )
        EventModelRegistry.register(
            exclude=(WorkflowStateRuntimeProxy,), model=WorkflowState
        )
        EventModelRegistry.register(model=WorkflowStateAction)
        EventModelRegistry.register(model=WorkflowStateEscalation)
        EventModelRegistry.register(model=WorkflowTransition)
        EventModelRegistry.register(model=WorkflowTransitionField)
        EventModelRegistry.register(model=WorkflowTransitionTriggerEvent)

        WorkflowAction.load_modules()

        ModelCopy(model=WorkflowState).add_fields(
            field_names=(
                'actions', 'workflow', 'label', 'final', 'initial',
                'completion'
            )
        )
        ModelCopy(model=WorkflowStateAction).add_fields(
            field_names=(
                'state', 'label', 'enabled', 'when', 'backend_path',
                'backend_data', 'condition'
            )
        )
        ModelCopy(model=WorkflowTransition).add_fields(
            field_names=(
                'workflow', 'label', 'origin_state', 'destination_state',
                'condition', 'fields', 'trigger_events'
            ),
            field_value_gets={
                'origin_state': {
                    'workflow': '{workflow.pk}',
                    'label': '{instance.origin_state.label}'
                },
                'destination_state': {
                    'workflow': '{workflow.pk}',
                    'label': '{instance.destination_state.label}'
                }
            }
        )
        ModelCopy(
            model=WorkflowTransitionTriggerEvent
        ).add_fields(
            field_names=('transition', 'event_type')
        )
        ModelCopy(
            model=WorkflowTransitionField
        ).add_fields(
            field_names=(
                'transition', 'field_type', 'name', 'label', 'help_text',
                'required', 'widget', 'widget_kwargs',
            )
        )
        ModelCopy(
            model=Workflow, bind_link=True, register_permission=True
        ).add_fields(
            field_names=(
                'auto_launch', 'internal_name', 'label', 'document_types',
                'states', 'transitions'
            )
        )

        ModelEventType.register(
            event_types=(
                event_workflow_instance_created,
                event_workflow_instance_transitioned,
            ), model=Document
        )
        ModelEventType.register(
            event_types=(event_workflow_template_edited,), model=Workflow
        )
        ModelEventType.register(
            event_types=(
                event_workflow_instance_created,
                event_workflow_instance_transitioned,
            ), model=WorkflowInstance
        )

        ModelProperty(
            model=Document,
            name='workflow.< workflow internal name >.get_current_state',
            label=_(message='Current state of a workflow'), description=_(
                message='Deprecated: Use `state_active` instead. Return '
                'the current state of the selected workflow.'
            )
        )
        ModelProperty(
            model=Document,
            name='workflow.< workflow internal name >.get_current_state.completion',
            label=_(message='Current completion of a workflow'),
            description=_(
                message='Deprecated: Use `state_active.completion` instead. '
                'Return the completion value of the current state of the '
                'selected workflow.'
            )
        )
        ModelProperty(
            model=Document,
            name='workflow.< workflow internal name >.state_active',
            label=_(message='Current state of a workflow'), description=_(
                message='Return the current state of the selected workflow.'
            )
        )
        ModelProperty(
            model=Document,
            name='workflow.< workflow internal name >.state_active.completion',
            label=_(message='Current completion of a workflow'),
            description=_(
                message='Return the completion value of the current state '
                'of the selected workflow.'
            )
        )

        ModelPermission.register(
            model=Document, permissions=(
                permission_workflow_instance_delete,
                permission_workflow_instance_transition,
                permission_workflow_template_view,
                permission_workflow_tools
            )
        )
        ModelPermission.register(
            model=Workflow, permissions=(
                permission_error_log_entry_view,
                permission_workflow_instance_delete,
                permission_workflow_instance_transition,
                permission_workflow_template_delete,
                permission_workflow_template_edit,
                permission_workflow_template_view, permission_workflow_tools
            )
        )
        ModelPermission.register(
            model=WorkflowTransition,
            permissions=(permission_workflow_instance_transition,)
        )

        ModelPermission.register_inheritance(
            model=WorkflowInstance, related='workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowInstanceLogEntry,
            related='workflow_instance__workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowState, related='workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowStateAction, related='state__workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowStateEscalation, related='state__workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowTransition, related='workflow',
        )
        ModelPermission.register_inheritance(
            model=WorkflowTransitionField, related='transition',
        )
        ModelPermission.register_inheritance(
            model=WorkflowTransitionTriggerEvent,
            related='transition__workflow',
        )

        ModelField(model=WorkflowInstance, name='document')
        ModelField(model=WorkflowInstance, name='state_active')
        ModelField(model=WorkflowInstance, name='workflow')

        ModelProperty(
            description=_(
                message='Return the last workflow instance log entry. The '
                'log entry itself has the following fields: datetime, '
                'transition, user, and comment.'
            ), label=_(message='Get last log entry'), model=WorkflowInstance,
            name='get_last_log_entry'
        )
        ModelProperty(
            description=_(
                message='Return the current context dictionary which '
                'includes runtime data from the workflow transition fields.'
            ), label=_(message='Get the context'), model=WorkflowInstance,
            name='get_runtime_context'
        )
        ModelProperty(
            description=_(
                message='Return the transition of the workflow instance.'
            ), label=_(message='Get last transition'), model=WorkflowInstance,
            name='get_last_transition'
        )

        ModelReverseField(
            description=_(
                message='A record of all state changes made to the '
                'workflow instance over time.'
            ), model=WorkflowInstance, name='log_entries'
        )

        ModelTemplating(
            model=WorkflowInstance, variable_name='workflow_instance'
        )


        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=Workflow
        )
        column_workflow_internal_name = SourceColumn(
            attribute='internal_name', include_label=True, is_sortable=True,
            source=Workflow
        )
        column_workflow_auto_launch = SourceColumn(
            attribute='auto_launch', include_label=True, is_sortable=True,
            source=Workflow, widget=column_widgets.TwoStateWidget
        )
        column_workflow_ignore_completed = SourceColumn(
            attribute='ignore_completed', include_label=True,
            is_sortable=True, source=Workflow,
            widget=column_widgets.TwoStateWidget
        )
        column_workflow_internal_name.add_exclude(
            source=WorkflowRuntimeProxy
        )
        column_workflow_get_state_initial = SourceColumn(
            attribute='get_state_initial', empty_value=_(message='None'),
            include_label=True, source=Workflow
        )
        column_workflow_get_state_final = SourceColumn(
            attribute='get_state_final', empty_value=_(message='None'),
            include_label=True, source=Workflow
        )


        column_workflow_get_state_final.add_exclude(
            source=WorkflowRuntimeProxy
        )
        column_workflow_get_state_initial.add_exclude(
            source=WorkflowRuntimeProxy
        )
        column_workflow_auto_launch.add_exclude(
            source=WorkflowRuntimeProxy
        )
        column_workflow_ignore_completed.add_exclude(
            source=WorkflowRuntimeProxy
        )
        SourceColumn(
            attribute='get_document_count', include_label=True,
            kwargs={'user': 'request.user'}, label=_(message='Documents'),
            order=99, source=WorkflowRuntimeProxy
        )


        SourceColumn(
            attribute='state_active', include_label=True,
            is_sortable=True, source=WorkflowInstance
        )
        SourceColumn(
            func=lambda context: getattr(
                context['object'].get_last_log_entry(), 'user',
                _(message='None')
            ), include_label=True, label=_(message='User'),
            source=WorkflowInstance
        )
        SourceColumn(
            attribute='get_last_transition', include_label=True,
            label=_(message='Last transition'), source=WorkflowInstance
        )
        SourceColumn(
            func=lambda context: getattr(
                context['object'].get_last_log_entry(), 'datetime',
                _(message='None')
            ), include_label=True, label=_(message='Date and time'),
            source=WorkflowInstance
        )
        SourceColumn(
            attribute='state_active__completion', include_label=True,
            is_sortable=True, label=_(message='Completion'),
            source=WorkflowInstance
        )


        SourceColumn(
            attribute='datetime', is_identifier=True,
            is_sortable=True, label=_(message='Date and time'),
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='user', include_label=True, label=_(message='User'),
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='get_origin_state', include_label=True,
            is_sortable=True, label=_(message='Origin state'),
            sort_field='transition__origin_state',
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='transition', include_label=True, is_sortable=True,
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='get_destination_state', include_label=True,
            is_sortable=True, label=_(message='Destination state'),
            sort_field='transition__destination_state',
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='comment', include_label=True, is_sortable=True,
            source=WorkflowInstanceLogEntry
        )
        SourceColumn(
            attribute='get_extra_data', include_label=True,
            label=_(message='Additional details'),
            source=WorkflowInstanceLogEntry, widget=WorkflowLogExtraDataWidget
        )


        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=WorkflowState
        )
        SourceColumn(
            attribute='initial', include_label=True, is_sortable=True,
            source=WorkflowState, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='final', include_label=True, is_sortable=True,
            source=WorkflowState, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='completion', include_label=True, is_sortable=True,
            source=WorkflowState
        )
        column_workflow_actions = SourceColumn(
            attribute='get_actions_display', include_label=True,
            source=WorkflowState
        )
        column_workflow_escalations = SourceColumn(
            attribute='get_escalations_display', include_label=True,
            source=WorkflowState
        )


        column_workflow_actions.add_exclude(
            source=WorkflowStateRuntimeProxy
        )
        column_workflow_escalations.add_exclude(
            source=WorkflowStateRuntimeProxy
        )

        SourceColumn(
            attribute='get_document_count', include_label=True,
            kwargs={'user': 'request.user'}, label=_(message='Documents'),
            order=99, source=WorkflowStateRuntimeProxy
        )


        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=WorkflowStateAction
        )
        SourceColumn(
            attribute='enabled', include_label=True, is_sortable=True,
            source=WorkflowStateAction, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_when_display', include_label=True,
            label=_(message='When?'), source=WorkflowStateAction
        )
        SourceColumn(
            attribute='get_backend_class_label', include_label=True,
            label=_(message='Action type'), source=WorkflowStateAction
        )
        SourceColumn(
            attribute='has_condition', include_label=True,
            source=WorkflowStateAction, widget=column_widgets.TwoStateWidget
        )


        SourceColumn(
            attribute='priority', is_identifier=True, is_sortable=True,
            source=WorkflowStateEscalation
        )
        SourceColumn(
            attribute='enabled', include_label=True, is_sortable=True,
            source=WorkflowStateEscalation, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='unit', include_label=True,
            source=WorkflowStateEscalation
        )
        SourceColumn(
            attribute='amount', include_label=True,
            source=WorkflowStateEscalation
        )
        SourceColumn(
            attribute='transition', include_label=True, is_sortable=True,
            source=WorkflowStateEscalation
        )
        SourceColumn(
            attribute='has_condition', include_label=True,
            source=WorkflowStateEscalation, widget=column_widgets.TwoStateWidget
        )


        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=WorkflowTransition,
        )
        SourceColumn(
            attribute='origin_state', include_label=True, is_sortable=True,
            source=WorkflowTransition
        )
        SourceColumn(
            attribute='destination_state', include_label=True,
            is_sortable=True, source=WorkflowTransition
        )
        SourceColumn(
            attribute='has_condition', include_label=True,
            source=WorkflowTransition, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_field_display', include_label=True,
            source=WorkflowTransition
        )
        SourceColumn(
            attribute='trigger_events', help_text=_(
                message='Triggers are system events that will cause the '
                'transition to be applied.'
            ), include_label=True, label=_(message='Triggers'),
            source=WorkflowTransition,
            widget=WorkflowTemplateTransitionTriggerColumnWidget
        )


        SourceColumn(
            attribute='name', is_identifier=True, is_sortable=True,
            source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='label', include_label=True, is_sortable=True,
            source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='get_field_type_display', include_label=True,
            label=_(message='Type'), source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='required', include_label=True, is_sortable=True,
            source=WorkflowTransitionField, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='has_default', include_label=True,
            source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='has_lookup', include_label=True,
            source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='get_widget_display', include_label=True,
            label=_(message='Widget'), is_sortable=False,
            source=WorkflowTransitionField
        )
        SourceColumn(
            attribute='widget_kwargs', include_label=True, is_sortable=True,
            source=WorkflowTransitionField
        )


        menu_list_facet.bind_links(
            links=(link_workflow_instance_list,), sources=(Document,)
        )
        menu_list_facet.bind_links(
            links=(link_workflow_instance_detail,),
            sources=(WorkflowInstance,)
        )
        menu_object.bind_links(
            links=(
                link_workflow_instance_delete_single,
                link_workflow_instance_transition,
            ), sources=(WorkflowInstance,)
        )
        menu_secondary.bind_links(
            links=(link_document_workflow_templates_launch_single,),
            sources=(
                WorkflowInstance,
                'document_states:document_multiple_workflow_templates_launch',
                'document_states:document_single_workflow_templates_launch',
                'document_states:workflow_instance_list'
            )
        )


        menu_list_facet.bind_links(
            links=(
                link_workflow_runtime_proxy_document_list,
                link_workflow_runtime_proxy_state_list,
            ), sources=(WorkflowRuntimeProxy,)
        )
        menu_list_facet.bind_links(
            links=(
                link_workflow_runtime_proxy_state_document_list,
            ), sources=(WorkflowStateRuntimeProxy,)
        )


        menu_main.bind_links(
            links=(link_workflow_runtime_proxy_list,), position=20
        )
        menu_list_facet.bind_links(
            links=(
                link_workflow_template_transition_triggers,
                link_workflow_template_transition_field_list,
            ), sources=(WorkflowTransition,)
        )
        menu_list_facet.bind_links(
            links=(
                link_document_type_workflow_template_list,
            ), sources=(DocumentType,)
        )
        menu_list_facet.bind_links(
            exclude=(WorkflowRuntimeProxy,),
            links=(
                link_workflow_template_document_type_list,
                link_workflow_template_state_list,
                link_workflow_template_transition_list,
                link_workflow_template_preview
            ), sources=(Workflow,)
        )
        menu_multi_item.bind_links(
            links=(link_document_workflow_templates_launch_multiple,),
            sources=(Document,)
        )
        menu_multi_item.bind_links(
            links=(link_workflow_template_delete_multiple,),
            sources=(Workflow,)
        )
        menu_object.bind_links(
            exclude=(WorkflowRuntimeProxy,), links=(
                link_workflow_template_delete_single,
                link_workflow_template_edit,
                link_workflow_template_launch
            ), sources=(Workflow,)
        )
        menu_related.bind_links(
            links=(link_workflow_template_list,), sources=(
                DocumentType, 'documents:document_type_list',
                'documents:document_type_create'
            )
        )
        menu_related.bind_links(
            exclude=(WorkflowRuntimeProxy,),
            links=(link_document_type_list,),
            sources=(
                Workflow, 'document_states:workflow_template_create',
                'document_states:workflow_template_list'
            )
        )
        menu_return.bind_links(
            exclude=(WorkflowRuntimeProxy,), links=(
                link_workflow_template_list,
            ), sources=(
                Workflow, 'document_states:workflow_template_create',
                'document_states:workflow_template_list'
            )
        )
        menu_secondary.bind_links(
            exclude=(WorkflowRuntimeProxy,), links=(
                link_workflow_template_create,
            ), sources=(
                Workflow, 'document_states:workflow_template_create',
                'document_states:workflow_template_list'
            )
        )
        menu_setup.bind_links(
            links=(link_workflow_template_setup,)
        )
        menu_tools.bind_links(
            links=(link_tool_launch_workflows,)
        )


        menu_object.bind_links(
            links=(
                link_workflow_template_state_escalation_edit,
                link_workflow_template_state_escalation_delete,
            ), sources=(WorkflowStateEscalation,)
        )


        menu_list_facet.bind_links(
            exclude=(WorkflowStateRuntimeProxy,),
            links=(
                link_workflow_template_state_action_list,
                link_workflow_template_state_escalation_list
            ), sources=(WorkflowState,)
        )
        menu_object.bind_links(
            exclude=(WorkflowStateRuntimeProxy,),
            links=(
                link_workflow_template_state_edit,
                link_workflow_template_state_delete
            ), sources=(WorkflowState,)
        )
        menu_secondary.bind_links(
            links=(
                link_workflow_template_state_action_selection,
                link_workflow_template_state_escalation_create
            ), sources=(WorkflowState,)
        )
        menu_secondary.bind_links(
            links=(link_workflow_template_state_create,), sources=(
                WorkflowState,
                'document_states:workflow_template_state_create',
                'document_states:workflow_template_state_list'
            )
        )


        menu_object.bind_links(
            links=(
                link_workflow_template_state_action_edit,
                link_workflow_template_state_action_delete,
            ), sources=(WorkflowStateAction,)
        )


        menu_object.bind_links(
            links=(
                link_workflow_template_transition_edit,
                link_workflow_template_transition_delete
            ), sources=(WorkflowTransition,)
        )
        menu_secondary.bind_links(
            links=(link_workflow_template_transition_field_create,),
            sources=(WorkflowTransition,)
        )


        menu_object.bind_links(
            links=(
                link_workflow_template_transition_field_delete,
                link_workflow_template_transition_field_edit
            ), sources=(WorkflowTransitionField,)
        )
        menu_secondary.bind_links(
            links=(link_workflow_template_transition_create,), sources=(
                WorkflowTransition,
                'document_states:workflow_template_transition_create',
                'document_states:workflow_template_transition_list'
            )
        )

        post_migrate.connect(
            dispatch_uid='workflows_handler_create_workflow_image_cache',
            receiver=handler_create_workflow_image_cache, sender=self
        )
        post_save.connect(
            dispatch_uid='workflows_handler_launch_workflow_on_create',
            receiver=handler_launch_workflow_on_create,
            sender=Document
        )
        signal_post_document_type_change.connect(
            dispatch_uid='workflows_handler_launch_workflow_on_type_change',
            receiver=handler_launch_workflow_on_type_change,
            sender=Document
        )


        post_save.connect(
            dispatch_uid='workflows_handler_transition_trigger',
            receiver=handler_transition_trigger,
            sender=Action
        )


        post_save.connect(
            dispatch_uid='workflows_handler_workflow_template_post_edit',
            receiver=handler_workflow_template_post_edit,
            sender=Workflow
        )


        post_save.connect(
            dispatch_uid='workflows_handler_workflow_template_state_post_edit',
            receiver=handler_workflow_template_state_post_edit,
            sender=WorkflowState
        )
        pre_delete.connect(
            dispatch_uid='workflows_handler_workflow_template_state_pre_delete',
            receiver=handler_workflow_template_state_pre_delete,
            sender=WorkflowState
        )


        post_save.connect(
            dispatch_uid='workflows_handler_workflow_template_transition_post_edit',
            receiver=handler_workflow_template_transition_post_edit,
            sender=WorkflowTransition
        )
        pre_delete.connect(
            dispatch_uid='workflows_handler_workflow_template_transition_pre_delete',
            receiver=handler_workflow_template_transition_pre_delete,
            sender=WorkflowTransition
        )
