from django.utils.translation import gettext_lazy as _

from mayan.apps.document_states.classes import WorkflowAction

from .models.document_type_models import DocumentType


class DocumentTypeChangeAction(WorkflowAction):
    form_field_widgets = {
        'document_type': {
            'class': 'django.forms.widgets.Select', 'kwargs': {
                'attrs': {'class': 'select2'}
            }
        }
    }
    form_fields = {
        'document_type': {
            'label': _(message='Document type'),
            'class': 'django.forms.ModelChoiceField', 'kwargs': {
                'help_text': _(
                    message='New document type for the workflow document.'
                ), 'queryset': DocumentType.objects.all(), 'required': True
            }
        }
    }
    label = _(message='Change document type')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Document type'), {
                    'fields': ('document_type',)
                }
            ),
        )
        return fieldsets

    def execute(self, context):
        context['workflow_instance'].document._document_type_change(
            document_type=self.get_document_type()
        )

    def get_document_type(self):
        return DocumentType.objects.get(
            pk=self.kwargs.get('document_type')
        )


class TrashDocumentAction(WorkflowAction):
    label = _(message='Send document to trash')

    def execute(self, context):
        workflow_instance = context['workflow_instance']
        document = workflow_instance.document

        if not document.in_trash:
            document.delete()
