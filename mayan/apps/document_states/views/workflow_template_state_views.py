from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.views import (
    ViewSingleObjectDynamicFormModelBackendCreate,
    ViewSingleObjectDynamicFormModelBackendEdit
)
from mayan.apps.views.generics import (
    FormView, SingleObjectCreateView, SingleObjectDeleteView,
    SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..classes import WorkflowAction
from ..forms.workflow_template_state_forms import (
    WorkflowTemplateStateActionDynamicForm,
    WorkflowTemplateStateActionSelectionForm, WorkflowTemplateStateForm
)
from ..icons import (
    icon_workflow_template_state, icon_workflow_template_state_action,
    icon_workflow_template_state_action_create,
    icon_workflow_template_state_action_delete,
    icon_workflow_template_state_action_edit,
    icon_workflow_template_state_action_list,
    icon_workflow_template_state_action_selection,
    icon_workflow_template_state_create, icon_workflow_template_state_delete,
    icon_workflow_template_state_edit, icon_workflow_template_state_list
)
from ..links import (
    link_workflow_template_state_action_selection,
    link_workflow_template_state_create
)
from ..models import Workflow, WorkflowState, WorkflowStateAction
from ..permissions import (
    permission_workflow_template_edit, permission_workflow_template_view
)


class WorkflowTemplateStateActionCreateView(
    ExternalObjectViewMixin, ViewSingleObjectDynamicFormModelBackendCreate
):
    backend_class = WorkflowAction
    external_object_class = WorkflowState
    external_object_permission = permission_workflow_template_edit
    external_object_pk_url_kwarg = 'workflow_template_state_id'
    form_class = WorkflowTemplateStateActionDynamicForm
    view_icon = icon_workflow_template_state_action_create

    def get_extra_context(self):
        return {
            'navigation_object_list': ('object', 'workflow'),
            'object': self.external_object,
            'title': _(
                message='Create a "%(backend_label)s" workflow action for: '
                '%(workflow_state)s'
            ) % {
                'backend_label': self.get_backend_class().label,
                'workflow_state': self.external_object
            },
            'workflow': self.external_object.workflow
        }

    def get_form_extra_kwargs(self):
        return {
            'backend_class': self.get_backend_class(),
            'request': self.request,
            'user': self.request.user
        }

    def get_form_schema_extra_kwargs(self):
        return {'workflow_template_state': self.external_object}

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'backend_path': self.kwargs['backend_path'],
            'state': self.external_object
        }

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'workflow_template_state_id': self.external_object.pk
            },
            viewname='document_states:workflow_template_state_action_list'
        )


class WorkflowTemplateStateActionDeleteView(SingleObjectDeleteView):
    model = WorkflowStateAction
    object_permission = permission_workflow_template_edit
    pk_url_kwarg = 'workflow_template_state_action_id'
    view_icon = icon_workflow_template_state_action_delete

    def get_extra_context(self):
        return {
            'navigation_object_list': (
                'object', 'workflow_state', 'workflow'
            ),
            'object': self.object,
            'title': _(
                message='Delete workflow state action: %s'
            ) % self.object,
            'workflow': self.object.state.workflow,
            'workflow_state': self.object.state
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'workflow_template_state_id': self.object.state.pk
            },
            viewname='document_states:workflow_template_state_action_list'
        )


class WorkflowTemplateStateActionEditView(
    ViewSingleObjectDynamicFormModelBackendEdit
):
    form_class = WorkflowTemplateStateActionDynamicForm
    model = WorkflowStateAction
    object_permission = permission_workflow_template_edit
    pk_url_kwarg = 'workflow_template_state_action_id'
    view_icon = icon_workflow_template_state_action_edit

    def get_extra_context(self):
        return {
            'navigation_object_list': (
                'object', 'workflow_state', 'workflow'
            ),
            'object': self.object,
            'title': _(
                message='Edit workflow state action: %s'
            ) % self.object,
            'workflow': self.object.state.workflow,
            'workflow_state': self.object.state
        }

    def get_form_extra_kwargs(self):
        return {
            'backend_class': self.get_backend_class(),
            'request': self.request,
            'user': self.request.user
        }

    def get_form_schema_extra_kwargs(self):
        return {'workflow_template_state': self.object.state}

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'workflow_template_state_id': self.object.state.pk
            },
            viewname='document_states:workflow_template_state_action_list'
        )


class WorkflowTemplateStateActionListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_class = WorkflowState
    external_object_permission = permission_workflow_template_edit
    external_object_pk_url_kwarg = 'workflow_template_state_id'
    view_icon = icon_workflow_template_state_action_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'navigation_object_list': ('object', 'workflow'),
            'no_results_icon': icon_workflow_template_state_action,
            'no_results_main_link': link_workflow_template_state_action_selection.resolve(
                context=RequestContext(
                    dict_={
                        'object': self.external_object
                    }, request=self.request
                )
            ),
            'no_results_text': _(
                message='Workflow state actions are macros that get executed '
                'when documents enters or leaves the state in which they '
                'reside.'
            ),
            'no_results_title': _(
                message='There are no actions for this workflow state'
            ),
            'object': self.external_object,
            'title': _(
                message='Actions for workflow state: %s'
            ) % self.external_object,
            'workflow': self.external_object.workflow
        }

    def get_source_queryset(self):
        return self.external_object.actions.all()


class WorkflowTemplateStateActionSelectionView(
    ExternalObjectViewMixin, FormView
):
    external_object_class = WorkflowState
    external_object_permission = permission_workflow_template_edit
    external_object_pk_url_kwarg = 'workflow_template_state_id'
    form_class = WorkflowTemplateStateActionSelectionForm
    view_icon = icon_workflow_template_state_action_selection

    def get_extra_context(self):
        return {
            'navigation_object_list': (
                'object', 'workflow'
            ),
            'object': self.external_object,
            'submit_label': _(message='Next'),
            'title': _(
                message='New workflow state action selection for: %s'
            ) % self.external_object,
            'workflow': self.external_object.workflow
        }

    def form_valid(self, form):
        klass = form.cleaned_data['klass']
        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={
                    'workflow_template_state_id': self.external_object.pk,
                    'backend_path': klass
                },
                viewname='document_states:workflow_template_state_action_create'
            )
        )


class WorkflowTemplateStateCreateView(
    ExternalObjectViewMixin, SingleObjectCreateView
):
    external_object_class = Workflow
    external_object_permission = permission_workflow_template_edit
    external_object_pk_url_kwarg = 'workflow_template_id'
    form_class = WorkflowTemplateStateForm
    view_icon = icon_workflow_template_state_create

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='Create states for workflow: %s'
            ) % self.external_object,
            'workflow': self.external_object
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'workflow': self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.states.all()

    def get_success_url(self):
        return reverse(
            kwargs={
                'workflow_template_id': self.kwargs['workflow_template_id']
            },
            viewname='document_states:workflow_template_state_list'
        )


class WorkflowTemplateStateDeleteView(SingleObjectDeleteView):
    model = WorkflowState
    object_permission = permission_workflow_template_edit
    pk_url_kwarg = 'workflow_template_state_id'
    view_icon = icon_workflow_template_state_delete

    def get_extra_context(self):
        return {
            'navigation_object_list': ('object', 'workflow'),
            'object': self.object,
            'title': _(
                message='Delete workflow state: %s?'
            ) % self.object,
            'workflow': self.object.workflow
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_success_url(self):
        return reverse(
            kwargs={
                'workflow_template_id': self.object.workflow.pk
            },
            viewname='document_states:workflow_template_state_list'
        )


class WorkflowTemplateStateEditView(SingleObjectEditView):
    form_class = WorkflowTemplateStateForm
    model = WorkflowState
    object_permission = permission_workflow_template_edit
    pk_url_kwarg = 'workflow_template_state_id'
    view_icon = icon_workflow_template_state_edit

    def get_extra_context(self):
        return {
            'navigation_object_list': ('object', 'workflow'),
            'object': self.object,
            'title': _(
                message='Edit workflow state: %s'
            ) % self.object,
            'workflow': self.object.workflow
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_success_url(self):
        return reverse(
            kwargs={'workflow_template_id': self.object.workflow.pk},
            viewname='document_states:workflow_template_state_list'
        )


class WorkflowTemplateStateListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_class = Workflow
    external_object_permission = permission_workflow_template_view
    external_object_pk_url_kwarg = 'workflow_template_id'
    view_icon = icon_workflow_template_state_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_workflow_template_state,
            'no_results_main_link': link_workflow_template_state_create.resolve(
                context=RequestContext(
                    dict_={'workflow': self.external_object},
                    request=self.request
                )
            ),
            'no_results_text': _(
                message='Create states and link them using transitions.'
            ),
            'no_results_title': _(
                message='This workflow doesn\'t have any states'
            ),
            'object': self.external_object,
            'title': _(
                message='States of workflow: %s'
            ) % self.external_object,
            'workflow': self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.states.all()
