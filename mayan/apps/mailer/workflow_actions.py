from django.utils.translation import gettext_lazy as _

from mayan.apps.document_states.classes import WorkflowAction

from .workflow_action_mixins import ObjectEmailActionMixin


class DocumentEmailAction(ObjectEmailActionMixin, WorkflowAction):
    label = _(message='Send document via email')
    previous_dotted_paths = (
        'mayan.apps.mailer.workflow_actions.EmailAction',
    )

    @classmethod
    def get_form_fields(cls, *args, **kwargs):
        fields = super().get_form_fields(*args, **kwargs)

        fields.update(
            {
                'attachment': {
                    'label': _(message='Attachment'),
                    'class': 'django.forms.BooleanField', 'default': False,
                    'help_text': _(
                        message='Attach the exported document version '
                        'to the email.'
                    ),
                    'required': False
                }
            }
        )

        return fields

    def get_execute_data(self, context):
        result = super().get_execute_data(context=context)
        document = self.get_object(context=context)

        if self.kwargs.get('attachment', False):
            if document.version_active:
                obj = document.version_active
                result.update(
                    {
                        'as_attachment': True,
                        'obj': obj
                    }
                )

        return result

    def get_object(self, context):
        return context['workflow_instance'].document
