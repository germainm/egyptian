from mayan.apps.rest_api import generics

from ..permissions import (
    permission_workflow_template_edit, permission_workflow_template_view
)
from ..serializers.workflow_template_transition_serializers import (
    WorkflowTemplateTransitionSerializer
)

from .api_view_mixins import ParentObjectWorkflowTemplateAPIViewMixin


class APIWorkflowTemplateTransitionListView(
    ParentObjectWorkflowTemplateAPIViewMixin, generics.ListCreateAPIView
):
    """
    get: Returns a list of all the workflow template transitions.
    post: Create a new workflow template transition.
    """
    mayan_external_object_permission_map = {
        'GET': permission_workflow_template_view,
        'POST': permission_workflow_template_edit
    }
    serializer_class = WorkflowTemplateTransitionSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'workflow': self.get_workflow_template()
        }

    def get_source_queryset(self):
        return self.get_workflow_template().transitions.all()


class APIWorkflowTemplateTransitionDetailView(
    ParentObjectWorkflowTemplateAPIViewMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected workflow template transition.
    get: Return the details of the selected workflow template transition.
    patch: Edit the selected workflow template transition.
    put: Edit the selected workflow template transition.
    """
    mayan_object_permission_map = {
        'DELETE': permission_workflow_template_edit,
        'GET': permission_workflow_template_view,
        'PATCH': permission_workflow_template_edit,
        'PUT': permission_workflow_template_edit
    }
    lookup_url_kwarg = 'workflow_template_transition_id'
    serializer_class = WorkflowTemplateTransitionSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'workflow': self.get_workflow_template()
        }

    def get_source_queryset(self):
        return self.get_workflow_template().transitions.all()
