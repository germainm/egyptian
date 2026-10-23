from mayan.apps.rest_api import generics

from ..permissions import (
    permission_workflow_template_edit, permission_workflow_template_view
)
from ..serializers.workflow_template_transition_field_serializers import (
    WorkflowTransitionFieldSerializer
)

from .api_view_mixins import (
    ParentObjectWorkflowTemplateTransitionAPIViewMixin
)


class APIWorkflowTemplateTransitionFieldListView(
    ParentObjectWorkflowTemplateTransitionAPIViewMixin,
    generics.ListCreateAPIView
):
    """
    get: Returns a list of all the workflow template transition fields.
    post: Create a new workflow template transition field.
    """
    mayan_external_object_permission_map = {
        'GET': permission_workflow_template_view,
        'POST': permission_workflow_template_edit
    }
    serializer_class = WorkflowTransitionFieldSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'transition': self.get_workflow_template_transition()
        }

    def get_source_queryset(self):
        return self.get_workflow_template_transition().fields.all()


class APIWorkflowTemplateTransitionFieldDetailView(
    ParentObjectWorkflowTemplateTransitionAPIViewMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected workflow template transition field.
    get: Return the details of the selected workflow template transition field.
    patch: Edit the selected workflow template transition field.
    put: Edit the selected workflow template transition field.
    """
    mayan_object_permission_map = {
        'DELETE': permission_workflow_template_edit,
        'GET': permission_workflow_template_view,
        'PATCH': permission_workflow_template_edit,
        'PUT': permission_workflow_template_edit
    }
    lookup_url_kwarg = 'workflow_template_transition_field_id'
    serializer_class = WorkflowTransitionFieldSerializer

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        return self.get_workflow_template_transition().fields.all()
