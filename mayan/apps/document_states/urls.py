from django.urls import re_path

from .api_views.workflow_instance_api_views import (
    APIWorkflowInstanceDetailView, APIWorkflowInstanceLaunchActionView,
    APIWorkflowInstanceListView, APIWorkflowInstanceLogEntryDetailView,
    APIWorkflowInstanceLogEntryListView,
    APIWorkflowInstanceLogEntryTransitionListView
)
from .api_views.workflow_template_api_views import (
    APIWorkflowTemplateDetailView, APIWorkflowTemplateDocumentListView,
    APIWorkflowTemplateDocumentTypeAddView,
    APIWorkflowTemplateDocumentTypeListView,
    APIWorkflowTemplateDocumentTypeRemoveView, APIWorkflowTemplateImageView,
    APIWorkflowTemplateListView
)
from .api_views.workflow_template_state_api_views import (
    APIWorkflowTemplateStateActionDetailView,
    APIWorkflowTemplateStateActionListView,
    APIWorkflowTemplateStateDocumentListView,
    APIWorkflowTemplateStateListView, APIWorkflowTemplateStateView
)
from .api_views.workflow_template_state_escalation_api_views import (
    APIWorkflowTemplateStateEscalationListView,
    APIWorkflowTemplateStateEscalationDetailView
)
from .api_views.workflow_template_transition_api_views import (
    APIWorkflowTemplateTransitionDetailView,
    APIWorkflowTemplateTransitionListView
)
from .api_views.workflow_template_transition_field_api_views import (
    APIWorkflowTemplateTransitionFieldDetailView,
    APIWorkflowTemplateTransitionFieldListView
)
from .api_views.workflow_template_transition_trigger_api_views import (
    APIWorkflowTemplateTransitionTriggerDetailView,
    APIWorkflowTemplateTransitionTriggerListView
)
from .views.workflow_instance_views import (
    WorkflowInstanceDeleteView, WorkflowInstanceDetailView,
    WorkflowInstanceListView, WorkflowInstanceTransitionExecuteView,
    WorkflowInstanceTransitionSelectView
)
from .views.workflow_proxy_views import (
    WorkflowRuntimeProxyDocumentListView, WorkflowRuntimeProxyListView,
    WorkflowRuntimeProxyStateDocumentListView,
    WorkflowRuntimeProxyStateListView
)
from .views.workflow_template_state_escalation_views import (
    WorkflowTemplateStateEscalationCreateView,
    WorkflowTemplateStateEscalationDeleteView,
    WorkflowTemplateStateEscalationEditView,
    WorkflowTemplateStateEscalationListView
)
from .views.workflow_template_state_views import (
    WorkflowTemplateStateActionCreateView,
    WorkflowTemplateStateActionDeleteView,
    WorkflowTemplateStateActionEditView, WorkflowTemplateStateActionListView,
    WorkflowTemplateStateActionSelectionView, WorkflowTemplateStateCreateView,
    WorkflowTemplateStateDeleteView, WorkflowTemplateStateEditView,
    WorkflowTemplateStateListView
)
from .views.workflow_template_transition_field_views import (
    WorkflowTemplateTransitionFieldCreateView,
    WorkflowTemplateTransitionFieldDeleteView,
    WorkflowTemplateTransitionFieldEditView,
    WorkflowTemplateTransitionFieldListView
)
from .views.workflow_template_transition_trigger_views import (
    WorkflowTemplateTransitionTriggerEventListView
)
from .views.workflow_template_transition_views import (
    WorkflowTemplateTransitionCreateView,
    WorkflowTemplateTransitionDeleteView, WorkflowTemplateTransitionEditView,
    WorkflowTemplateTransitionListView
)
from .views.workflow_template_views import (
    DocumentTypeWorkflowTemplateAddRemoveView,
    DocumentWorkflowTemplatesLaunchView, ToolLaunchWorkflows,
    WorkflowTemplateCreateView, WorkflowTemplateDeleteView,
    WorkflowTemplateDocumentTypeAddRemoveView, WorkflowTemplateEditView,
    WorkflowTemplateLaunchView, WorkflowTemplateListView,
    WorkflowTemplatePreviewView
)

urlpatterns_workflow_instances = [
    re_path(
        route=r'^documents/(?P<document_id>\d+)/workflows/$',
        name='workflow_instance_list',
        view=WorkflowInstanceListView.as_view()
    ),
    re_path(
        route=r'^documents/workflows/(?P<workflow_instance_id>\d+)/delete/$',
        name='workflow_instance_delete_single',
        view=WorkflowInstanceDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/workflows/(?P<workflow_instance_id>\d+)/$',
        name='workflow_instance_detail',
        view=WorkflowInstanceDetailView.as_view()
    ),
    re_path(
        route=r'^documents/workflows/(?P<workflow_instance_id>\d+)/transitions/select/$',
        name='workflow_instance_transition_selection',
        view=WorkflowInstanceTransitionSelectView.as_view()
    ),
    re_path(
        route=r'^documents/workflows/(?P<workflow_instance_id>\d+)/transitions/(?P<workflow_template_transition_id>\d+)/execute/$',
        name='workflow_instance_transition_execute',
        view=WorkflowInstanceTransitionExecuteView.as_view()
    )
]

urlpatterns_workflow_runtime_proxies = [
    re_path(
        route=r'^workflow_runtime_proxies/$',
        name='workflow_runtime_proxy_list',
        view=WorkflowRuntimeProxyListView.as_view()
    ),
    re_path(
        route=r'^workflow_runtime_proxies/(?P<workflow_runtime_proxy_id>\d+)/documents/$',
        name='workflow_runtime_proxy_document_list',
        view=WorkflowRuntimeProxyDocumentListView.as_view()
    ),
    re_path(
        route=r'^workflow_runtime_proxies/(?P<workflow_runtime_proxy_id>\d+)/states/$',
        name='workflow_runtime_proxy_state_list',
        view=WorkflowRuntimeProxyStateListView.as_view()
    ),
    re_path(
        route=r'^workflow_runtime_proxies/states/(?P<workflow_runtime_proxy_state_id>\d+)/documents/$',
        name='workflow_runtime_proxy_state_document_list',
        view=WorkflowRuntimeProxyStateDocumentListView.as_view()
    )
]

urlpatterns_workflow_states = [
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/states/$',
        name='workflow_template_state_list',
        view=WorkflowTemplateStateListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/states/create/$',
        name='workflow_template_state_create',
        view=WorkflowTemplateStateCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/delete/$',
        name='workflow_template_state_delete',
        view=WorkflowTemplateStateDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/edit/$',
        name='workflow_template_state_edit',
        view=WorkflowTemplateStateEditView.as_view()
    )
]

urlpatterns_workflow_state_actions = [
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/actions/$',
        name='workflow_template_state_action_list',
        view=WorkflowTemplateStateActionListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/actions/selection/$',
        name='workflow_template_state_action_selection',
        view=WorkflowTemplateStateActionSelectionView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/actions/(?P<backend_path>[a-zA-Z0-9_.]+)/create/$',
        name='workflow_template_state_action_create',
        view=WorkflowTemplateStateActionCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/actions/(?P<workflow_template_state_action_id>\d+)/delete/$',
        name='workflow_template_state_action_delete',
        view=WorkflowTemplateStateActionDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/actions/(?P<workflow_template_state_action_id>\d+)/edit/$',
        name='workflow_template_state_action_edit',
        view=WorkflowTemplateStateActionEditView.as_view()
    )
]

urlpatterns_workflow_state_escalations = [
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/escalations/$',
        name='workflow_template_state_escalation_list',
        view=WorkflowTemplateStateEscalationListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/(?P<workflow_template_state_id>\d+)/escalations/create/$',
        name='workflow_template_state_escalation_create',
        view=WorkflowTemplateStateEscalationCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/escalations/(?P<workflow_template_state_escalation_id>\d+)/delete/$',
        name='workflow_template_state_escalation_delete',
        view=WorkflowTemplateStateEscalationDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/states/escalations/(?P<workflow_template_state_escalation_id>\d+)/edit/$',
        name='workflow_template_state_escalation_edit',
        view=WorkflowTemplateStateEscalationEditView.as_view()
    )
]

urlpatterns_workflow_templates = [
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/workflow_templates/$',
        name='document_type_workflow_templates',
        view=DocumentTypeWorkflowTemplateAddRemoveView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/workflow_templates/launch/$',
        name='document_single_workflow_templates_launch',
        view=DocumentWorkflowTemplatesLaunchView.as_view()
    ),
    re_path(
        route=r'^documents/multiple/workflow_templates/launch/$',
        name='document_multiple_workflow_templates_launch',
        view=DocumentWorkflowTemplatesLaunchView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/$', name='workflow_template_list',
        view=WorkflowTemplateListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/create/$',
        name='workflow_template_create',
        view=WorkflowTemplateCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/delete/$',
        name='workflow_template_single_delete',
        view=WorkflowTemplateDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/multiple/delete/$',
        name='workflow_template_multiple_delete',
        view=WorkflowTemplateDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/document_types/$',
        name='workflow_template_document_types',
        view=WorkflowTemplateDocumentTypeAddRemoveView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/edit/$',
        name='workflow_template_edit',
        view=WorkflowTemplateEditView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/launch/$',
        name='workflow_template_launch',
        view=WorkflowTemplateLaunchView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/preview/$',
        name='workflow_template_preview',
        view=WorkflowTemplatePreviewView.as_view()
    )
]

urlpatterns_workflow_transitions = [
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/transitions/$',
        name='workflow_template_transition_list',
        view=WorkflowTemplateTransitionListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/transitions/create/$',
        name='workflow_template_transition_create',
        view=WorkflowTemplateTransitionCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/(?P<workflow_template_transition_id>\d+)/delete/$',
        name='workflow_template_transition_delete',
        view=WorkflowTemplateTransitionDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/(?P<workflow_template_transition_id>\d+)/edit/$',
        name='workflow_template_transition_edit',
        view=WorkflowTemplateTransitionEditView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/(?P<workflow_template_transition_id>\d+)/events/$',
        name='workflow_template_transition_triggers',
        view=WorkflowTemplateTransitionTriggerEventListView.as_view()
    )
]

urlpatterns_workflow_transition_fields = [
    re_path(
        route=r'^workflow_templates/transitions/(?P<workflow_template_transition_id>\d+)/fields/create/$',
        name='workflow_template_transition_field_create',
        view=WorkflowTemplateTransitionFieldCreateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/(?P<workflow_template_transition_id>\d+)/fields/$',
        name='workflow_template_transition_field_list',
        view=WorkflowTemplateTransitionFieldListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/fields/(?P<workflow_template_transition_field_id>\d+)/delete/$',
        name='workflow_template_transition_field_delete',
        view=WorkflowTemplateTransitionFieldDeleteView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/transitions/fields/(?P<workflow_template_transition_field_id>\d+)/edit/$',
        name='workflow_template_transition_field_edit',
        view=WorkflowTemplateTransitionFieldEditView.as_view()
    )
]

urlpatterns_tools = [
    re_path(
        route=r'^tools/workflows/launch/$', name='tool_launch_workflows',
        view=ToolLaunchWorkflows.as_view()
    )
]

urlpatterns = []
urlpatterns.extend(urlpatterns_tools)
urlpatterns.extend(urlpatterns_workflow_instances)
urlpatterns.extend(urlpatterns_workflow_runtime_proxies)
urlpatterns.extend(urlpatterns_workflow_states)
urlpatterns.extend(urlpatterns_workflow_state_actions)
urlpatterns.extend(urlpatterns_workflow_state_escalations)
urlpatterns.extend(urlpatterns_workflow_templates)
urlpatterns.extend(urlpatterns_workflow_transitions)
urlpatterns.extend(urlpatterns_workflow_transition_fields)

api_urls = [
    re_path(
        route=r'^workflow_templates/$', name='workflow-template-list',
        view=APIWorkflowTemplateListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/$',
        name='workflow-template-detail', view=APIWorkflowTemplateDetailView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/documents/$',
        name='workflow-template-document-list',
        view=APIWorkflowTemplateDocumentListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/document_types/$',
        name='workflow-template-document-type-list',
        view=APIWorkflowTemplateDocumentTypeListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/document_types/add/$',
        name='workflow-template-document-type-add',
        view=APIWorkflowTemplateDocumentTypeAddView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/document_types/remove/$',
        name='workflow-template-document-type-remove',
        view=APIWorkflowTemplateDocumentTypeRemoveView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>\d+)/image/$',
        name='workflow-template-image',
        view=APIWorkflowTemplateImageView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/$',
        name='workflow-template-state-list',
        view=APIWorkflowTemplateStateListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/$',
        name='workflow-template-state-detail',
        view=APIWorkflowTemplateStateView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/actions/$',
        name='workflow-template-state-action-list',
        view=APIWorkflowTemplateStateActionListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/actions/(?P<workflow_template_state_action_id>[0-9]+)/$',
        name='workflow-template-state-action-detail',
        view=APIWorkflowTemplateStateActionDetailView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/documents/$',
        name='workflow-template-state-document-list',
        view=APIWorkflowTemplateStateDocumentListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/escalations/$',
        name='workflow-template-state-escalation-list',
        view=APIWorkflowTemplateStateEscalationListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/states/(?P<workflow_template_state_id>[0-9]+)/escalations/(?P<workflow_template_state_escalation_id>[0-9]+)/$',
        name='workflow-template-state-escalation-detail',
        view=APIWorkflowTemplateStateEscalationDetailView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/$',
        name='workflow-template-transition-list',
        view=APIWorkflowTemplateTransitionListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/(?P<workflow_template_transition_id>[0-9]+)/$',
        name='workflow-template-transition-detail',
        view=APIWorkflowTemplateTransitionDetailView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/(?P<workflow_template_transition_id>[0-9]+)/fields/$',
        name='workflow-template-transition-field-list',
        view=APIWorkflowTemplateTransitionFieldListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/(?P<workflow_template_transition_id>[0-9]+)/fields/(?P<workflow_template_transition_field_id>[0-9]+)/$',
        name='workflow-template-transition-field-detail',
        view=APIWorkflowTemplateTransitionFieldDetailView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/(?P<workflow_template_transition_id>[0-9]+)/triggers/$',
        name='workflow-template-transition-trigger-list',
        view=APIWorkflowTemplateTransitionTriggerListView.as_view()
    ),
    re_path(
        route=r'^workflow_templates/(?P<workflow_template_id>[0-9]+)/transitions/(?P<workflow_template_transition_id>[0-9]+)/triggers/(?P<workflow_template_transition_trigger_id>[0-9]+)/$',
        name='workflow-template-transition-trigger-detail',
        view=APIWorkflowTemplateTransitionTriggerDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/$',
        name='workflow-instance-list',
        view=APIWorkflowInstanceListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/launch/$',
        name='workflow-instance-launch',
        view=APIWorkflowInstanceLaunchActionView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/(?P<workflow_instance_id>[0-9]+)/$',
        name='workflow-instance-detail',
        view=APIWorkflowInstanceDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/(?P<workflow_instance_id>[0-9]+)/log_entries/$',
        name='workflow-instance-log-entry-list',
        view=APIWorkflowInstanceLogEntryListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/(?P<workflow_instance_id>[0-9]+)/log_entries/transitions/$',
        name='workflow-instance-log-entry-transition-list',
        view=APIWorkflowInstanceLogEntryTransitionListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/workflow_instances/(?P<workflow_instance_id>[0-9]+)/log_entries/(?P<workflow_instance_log_entry_id>[0-9]+)/$',
        name='workflow-instance-log-entry-detail',
        view=APIWorkflowInstanceLogEntryDetailView.as_view()
    )
]
