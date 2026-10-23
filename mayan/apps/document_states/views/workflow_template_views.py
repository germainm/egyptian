from django.contrib import messages
from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.views.generics import (
    AddRemoveView, ConfirmView, MultipleObjectDeleteView,
    MultipleObjectFormActionView, SingleObjectCreateView,
    SingleObjectDetailView, SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms.workflow_template_forms import (
    WorkflowTemplateForm, WorkflowTemplatePreviewForm,
    WorkflowTemplateSelectionForm
)
from ..icons import (
    icon_document_type_workflow_template_list,
    icon_document_workflow_templates_launch_multiple, icon_tool_launch_workflows,
    icon_workflow_template_create, icon_workflow_template_delete,
    icon_workflow_template_document_type_list, icon_workflow_template_edit,
    icon_workflow_template_launch, icon_workflow_template_list,
    icon_workflow_template_preview
)
from ..links import link_workflow_template_create
from ..models import Workflow
from ..permissions import (
    permission_workflow_template_create, permission_workflow_template_delete,
    permission_workflow_template_edit, permission_workflow_template_view,
    permission_workflow_tools
)
from ..tasks import (
    task_launch_all_workflows, task_launch_workflow, task_launch_workflow_for
)


class DocumentTypeWorkflowTemplateAddRemoveView(AddRemoveView):
    list_added_title = _(message='Workflows assigned this document type')
    list_available_title = _(message='Available workflows')
    main_object_method_add_name = 'workflow_templates_add'
    main_object_method_remove_name = 'workflow_templates_remove'
    main_object_model = DocumentType
    main_object_permission = permission_document_type_edit
    main_object_pk_url_kwarg = 'document_type_id'
    related_field = 'workflows'
    secondary_object_model = Workflow
    secondary_object_permission = permission_workflow_template_edit
    view_icon = icon_document_type_workflow_template_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'subtitle': _(
                message='Removing a workflow from a document type will also '
                'remove all running instances of that workflow.'
            ),
            'title': _(
                message='Workflows assigned the document type: %s'
            ) % self.main_object
        }


class DocumentWorkflowTemplatesLaunchView(MultipleObjectFormActionView):
    error_message = _(
        message='Error launching workflows for document "%(instance)s"; '
        '%(exception)s'
    )
    form_class = WorkflowTemplateSelectionForm
    object_permission = permission_workflow_tools
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_plural = _(
        message='Workflows queued for launch successfully for %(count)d '
        'documents.'
    )
    success_message_single = _(
        message='Workflows queued for launch successfully for document '
        '"%(object)s".'
    )
    success_message_singular = _(
        message='Workflows queued for launch successfully for %(count)d '
        'document.'
    )
    title_plural = _(
        message='Queue launching workflows for the selected %(count)d '
        'documents.'
    )
    title_single = _(message='Launch workflow: %(object)s.')
    title_singular = _(
        message='Queue launching workflows for the selected %(count)d '
        'document.'
    )
    view_icon = icon_document_workflow_templates_launch_multiple

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Launch'),
            'subtitle': _(
                message='Workflows already launched or workflows not '
                'applicable to some documents when multiple documents are '
                'selected, will be silently ignored.'
            )
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_form_extra_kwargs(self):
        workflows_union = Workflow.objects.filter(
            document_types__in=self.object_list.values('document_type')
        ).distinct()

        result = {
            'help_text': _(message='Workflows to be launched.'),
            'permission': permission_workflow_tools,
            'queryset': workflows_union,
            'user': self.request.user
        }

        return result

    def object_action(self, form, instance):
        queryset_workflows = AccessControlList.objects.restrict_queryset(
            permission=permission_workflow_tools,
            queryset=form.cleaned_data['workflows'], user=self.request.user
        )

        for workflow in queryset_workflows:
            task_launch_workflow_for.apply_async(
                kwargs={
                    'document_id': instance.pk,
                    'user_id': self.request.user.pk,
                    'workflow_id': workflow.pk
                }
            )


class WorkflowTemplateCreateView(SingleObjectCreateView):
    extra_context = {
        'title': _(message='Create workflow')
    }
    form_class = WorkflowTemplateForm
    model = Workflow
    post_action_redirect = reverse_lazy(
        viewname='document_states:workflow_template_list'
    )
    view_icon = icon_workflow_template_create
    view_permission = permission_workflow_template_create

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class WorkflowTemplateDeleteView(MultipleObjectDeleteView):
    error_message = _(
        message='Error deleting workflow "%(instance)s"; %(exception)s'
    )
    model = Workflow
    object_permission = permission_workflow_template_delete
    pk_url_kwarg = 'workflow_template_id'
    post_action_redirect = reverse_lazy(
        viewname='document_states:workflow_template_list'
    )
    success_message_plural = _(
        message='%(count)d workflows deleted successfully.'
    )
    success_message_single = _(
        message='Workflow "%(object)s" deleted successfully.'
    )
    success_message_singular = _(
        message='%(count)d workflow deleted successfully.'
    )
    title_plural = _(message='Delete the %(count)d selected workflows.')
    title_single = _(message='Delete workflow: %(object)s.')
    title_singular = _(message='Delete the %(count)d selected workflow.')
    view_icon = icon_workflow_template_delete

    def get_extra_context(self):
        return {
            'message': _(
                message='All workflow instances will also be deleted.'
            )
        }

    def object_action(self, instance, form=None):
        instance.delete()


class WorkflowTemplateEditView(SingleObjectEditView):
    form_class = WorkflowTemplateForm
    model = Workflow
    object_permission = permission_workflow_template_edit
    pk_url_kwarg = 'workflow_template_id'
    post_action_redirect = reverse_lazy(
        viewname='document_states:workflow_template_list'
    )
    view_icon = icon_workflow_template_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit workflow: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class WorkflowTemplateDocumentTypeAddRemoveView(AddRemoveView):
    list_added_title = _(message='Document types assigned this workflow')
    list_available_title = _(message='Available document types')
    main_object_method_add_name = 'document_types_add'
    main_object_method_remove_name = 'document_types_remove'
    main_object_model = Workflow
    main_object_permission = permission_workflow_template_edit
    main_object_pk_url_kwarg = 'workflow_template_id'
    related_field = 'document_types'
    secondary_object_model = DocumentType
    secondary_object_permission = permission_document_type_edit
    view_icon = icon_workflow_template_document_type_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'subtitle': _(
                message='Removing a document type from a workflow will also '
                'remove all running instances of that workflow for '
                'documents of the document type just removed.'
            ),
            'title': _(
                message='Document types assigned the workflow: %s'
            ) % self.main_object
        }


class WorkflowTemplateLaunchView(ExternalObjectViewMixin, ConfirmView):
    external_object_class = Workflow
    external_object_permission = permission_workflow_tools
    external_object_pk_url_kwarg = 'workflow_template_id'
    view_icon = icon_workflow_template_launch

    def get_extra_context(self):
        return {
            'subtitle': _(
                message='This will launch the workflow for documents that '
                'have already been uploaded.'
            ),
            'submit_label': _(message='Launch'),
            'title': _(message='Launch workflow?')
        }

    def view_action(self):
        task_launch_workflow.apply_async(
            kwargs={
                'user_id': self.request.user.pk,
                'workflow_id': self.external_object.pk
            }
        )
        messages.success(
            message=_(message='Workflow launch queued successfully.'),
            request=self.request
        )


class WorkflowTemplateListView(SingleObjectListView):
    model = Workflow
    object_permission = permission_workflow_template_view
    view_icon = icon_workflow_template_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_workflow_template_list,
            'no_results_main_link': link_workflow_template_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Workflows store a series of states and keep track '
                'of the current state of a document. Transitions are used to '
                'change the current state to a new one.'
            ),
            'no_results_title': _(
                message='No workflows have been defined'
            ),
            'title': _(message='Workflows')
        }


class WorkflowTemplatePreviewView(SingleObjectDetailView):
    form_class = WorkflowTemplatePreviewForm
    model = Workflow
    object_permission = permission_workflow_template_view
    pk_url_kwarg = 'workflow_template_id'
    view_icon = icon_workflow_template_preview

    def get_extra_context(self):
        return {
            'hide_labels': True,
            'object': self.object,
            'title': _(message='Preview of: %s') % self.object
        }


class ToolLaunchWorkflows(ConfirmView):
    extra_context = {
        'subtitle': _(
            message='This will launch all workflows created after documents '
            'have already been uploaded.'
        ),
        'submit_label': _(message='Launch'),
        'title': _(message='Launch all workflows?')
    }
    view_icon = icon_tool_launch_workflows
    view_permission = permission_workflow_tools

    def view_action(self):
        task_launch_all_workflows.apply_async(
            kwargs={'user_id': self.request.user.pk}
        )
        messages.success(
            message=_(message='Workflow launch queued successfully.'),
            request=self.request
        )
