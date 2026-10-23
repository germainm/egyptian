from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_type_workflow_template_list,
    icon_document_workflow_templates_launch_multiple,
    icon_document_workflow_templates_launch_single,
    icon_tool_launch_workflows,
    icon_workflow_instance_delete, icon_workflow_instance_detail,
    icon_workflow_instance_list, icon_workflow_instance_transition,
    icon_workflow_runtime_proxy_document_list,
    icon_workflow_runtime_proxy_list,
    icon_workflow_runtime_proxy_state_document_list,
    icon_workflow_runtime_proxy_state_list, icon_workflow_template_create,
    icon_workflow_template_delete, icon_workflow_template_document_type_list,
    icon_workflow_template_edit, icon_workflow_template_launch,
    icon_workflow_template_list, icon_workflow_template_preview,
    icon_workflow_template_state_action_delete,
    icon_workflow_template_state_action_edit,
    icon_workflow_template_state_action_list,
    icon_workflow_template_state_action_selection,
    icon_workflow_template_state_create, icon_workflow_template_state_delete,
    icon_workflow_template_state_edit, icon_workflow_template_state_list,
    icon_workflow_template_state_escalation_create,
    icon_workflow_template_state_escalation_delete,
    icon_workflow_template_state_escalation_edit,
    icon_workflow_template_state_escalation_list,
    icon_workflow_template_transition_create,
    icon_workflow_template_transition_delete,
    icon_workflow_template_transition_edit,
    icon_workflow_template_transition_triggers,
    icon_workflow_template_transition_field_create,
    icon_workflow_template_transition_field_delete,
    icon_workflow_template_transition_field_edit,
    icon_workflow_template_transition_field_list,
    icon_workflow_template_transition_list
)
from .permissions import (
    permission_workflow_template_create, permission_workflow_template_delete,
    permission_workflow_template_edit, permission_workflow_template_view,
    permission_workflow_tools
)


link_document_type_workflow_template_list = Link(
    args='resolved_object.pk',
    icon=icon_document_type_workflow_template_list,
    permission=permission_document_type_edit, text=_(message='Workflows'),
    view='document_states:document_type_workflow_templates'
)
link_workflow_template_create = Link(
    icon=icon_workflow_template_create,
    permission=permission_workflow_template_create,
    text=_(message='Create workflow'), view='document_states:workflow_template_create'
)
link_workflow_template_document_type_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_document_type_list,
    permission=permission_workflow_template_edit, text=_(message='Document types'),
    view='document_states:workflow_template_document_types'
)
link_workflow_template_delete_multiple = Link(
    icon=icon_workflow_template_delete,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_multiple_delete'
)
link_workflow_template_delete_single = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_delete,
    permission=permission_workflow_template_delete,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_single_delete'
)
link_workflow_template_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'), view='document_states:workflow_template_edit'
)
link_workflow_template_launch = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_launch,
    permission=permission_workflow_tools,
    text=_(message='Launch workflow'),
    view='document_states:workflow_template_launch'
)
link_workflow_template_list = Link(
    icon=icon_workflow_template_list, text=_(message='Workflows'),
    view='document_states:workflow_template_list'
)
link_workflow_template_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='document_states', model_name='Workflow',
        object_permission=permission_workflow_template_view,
        view_permission=permission_workflow_template_create,
    ), icon=icon_workflow_template_list, text=_(message='Workflows'),
    view='document_states:workflow_template_list'
)

link_workflow_template_preview = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_preview,
    permission=permission_workflow_template_view,
    text=_(message='Preview'), view='document_states:workflow_template_preview'
)


link_workflow_template_state_action_delete = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_action_delete,
    permission=permission_workflow_template_edit,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_state_action_delete'
)
link_workflow_template_state_action_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_action_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'),
    view='document_states:workflow_template_state_action_edit'
)
link_workflow_template_state_action_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_action_list,
    permission=permission_workflow_template_edit,
    text=_(message='Actions'),
    view='document_states:workflow_template_state_action_list'
)
link_workflow_template_state_action_selection = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_action_selection,
    permission=permission_workflow_template_edit,
    text=_(message='Create action'),
    view='document_states:workflow_template_state_action_selection'
)


link_workflow_template_state_escalation_create = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_escalation_create,
    permission=permission_workflow_template_edit,
    text=_(message='Create escalation'),
    view='document_states:workflow_template_state_escalation_create'
)
link_workflow_template_state_escalation_delete = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_escalation_delete,
    permission=permission_workflow_template_edit,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_state_escalation_delete'
)
link_workflow_template_state_escalation_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_escalation_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'),
    view='document_states:workflow_template_state_escalation_edit'
)
link_workflow_template_state_escalation_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_escalation_list,
    permission=permission_workflow_template_edit,
    text=_(message='Escalations'),
    view='document_states:workflow_template_state_escalation_list'
)


link_workflow_template_state_create = Link(
    args='workflow.pk',
    icon=icon_workflow_template_state_create,
    permission=permission_workflow_template_edit, text=_(message='Create state'),
    view='document_states:workflow_template_state_create'
)
link_workflow_template_state_delete = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_delete,
    permission=permission_workflow_template_edit,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_state_delete'
)
link_workflow_template_state_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'), view='document_states:workflow_template_state_edit'
)
link_workflow_template_state_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_state_list,
    permission=permission_workflow_template_view, text=_(message='States'),
    view='document_states:workflow_template_state_list'
)


link_workflow_template_transition_create = Link(
    args='workflow.pk',
    icon=icon_workflow_template_transition_create,
    permission=permission_workflow_template_edit,
    text=_(message='Create transition'),
    view='document_states:workflow_template_transition_create'
)
link_workflow_template_transition_delete = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_delete,
    permission=permission_workflow_template_edit,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_transition_delete'
)
link_workflow_template_transition_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'), view='document_states:workflow_template_transition_edit'
)
link_workflow_template_transition_triggers = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_triggers,
    permission=permission_workflow_template_edit,
    text=_(message='Transition triggers'),
    view='document_states:workflow_template_transition_triggers'
)
link_workflow_template_transition_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_list,
    permission=permission_workflow_template_view, text=_(message='Transitions'),
    view='document_states:workflow_template_transition_list'
)


link_document_workflow_templates_launch_multiple = Link(
    icon=icon_document_workflow_templates_launch_multiple,
    text=_(message='Launch workflows'),
    view='document_states:document_multiple_workflow_templates_launch'
)
link_document_workflow_templates_launch_single = Link(
    args='resolved_object.pk',
    icon=icon_document_workflow_templates_launch_single,
    permission=permission_workflow_tools, text=_(message='Launch workflows'),
    view='document_states:document_single_workflow_templates_launch'
)
link_workflow_template_transition_field_create = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_field_create,
    permission=permission_workflow_template_edit, text=_(message='Create field'),
    view='document_states:workflow_template_transition_field_create'
)
link_workflow_template_transition_field_delete = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_field_delete,
    permission=permission_workflow_template_edit,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_template_transition_field_delete'
)
link_workflow_template_transition_field_edit = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_field_edit,
    permission=permission_workflow_template_edit,
    text=_(message='Edit'),
    view='document_states:workflow_template_transition_field_edit'
)
link_workflow_template_transition_field_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_template_transition_field_list,
    permission=permission_workflow_template_edit,
    text=_(message='Fields'),
    view='document_states:workflow_template_transition_field_list'
)


link_workflow_instance_delete_single = Link(
    args='resolved_object.pk', icon=icon_workflow_instance_delete,
    tags='dangerous', text=_(message='Delete'),
    view='document_states:workflow_instance_delete_single'
)
link_workflow_instance_detail = Link(
    args='resolved_object.pk',
    icon=icon_workflow_instance_detail,
    permission=permission_workflow_template_view,
    text=_(message='Detail'), view='document_states:workflow_instance_detail'
)
link_workflow_instance_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_instance_list,
    permission=permission_workflow_template_view, text=_(message='Workflows'),
    view='document_states:workflow_instance_list'
)
link_workflow_instance_transition = Link(
    args='resolved_object.pk',
    icon=icon_workflow_instance_transition,
    text=_(message='Transition'),
    view='document_states:workflow_instance_transition_selection'
)


link_workflow_runtime_proxy_document_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_runtime_proxy_document_list,
    permission=permission_workflow_template_view,
    text=_(message='Workflow documents'),
    view='document_states:workflow_runtime_proxy_document_list'
)
link_workflow_runtime_proxy_list = Link(
    condition=factory_condition_queryset_access(
        app_label='document_states', model_name='WorkflowRuntimeProxy',
        object_permission=permission_workflow_template_view,
    ), icon=icon_workflow_runtime_proxy_list,
    text=_(message='Workflows'), view='document_states:workflow_runtime_proxy_list'
)
link_workflow_runtime_proxy_state_document_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_runtime_proxy_state_document_list,
    permission=permission_workflow_template_view,
    text=_(message='State documents'),
    view='document_states:workflow_runtime_proxy_state_document_list'
)
link_workflow_runtime_proxy_state_list = Link(
    args='resolved_object.pk',
    icon=icon_workflow_runtime_proxy_state_list,
    permission=permission_workflow_template_view, text=_(message='States'),
    view='document_states:workflow_runtime_proxy_state_list'
)


link_tool_launch_workflows = Link(
    icon=icon_tool_launch_workflows,
    permission=permission_workflow_tools,
    text=_(message='Launch all workflows'),
    view='document_states:tool_launch_workflows'
)
