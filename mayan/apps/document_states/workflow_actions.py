import json
import logging

import requests

from django.utils.translation import gettext_lazy as _

from mayan.apps.credentials.class_mixins import (
    BackendMixinCredentialsOptional
)

from .classes import WorkflowAction
from .exceptions import WorkflowStateActionError
from .literals import (
    DEFAULT_HTTP_ACTION_TIMEOUT, DEFAULT_HTTP_ACTION_VERIFY_CERTIFICATES,
    WORKFLOW_ACTION_HTTP_REQUEST_DEFAULT_RESPONSE_STORE_NAME
)
from .models.workflow_instance_models import WorkflowInstance
from .models.workflow_models import Workflow
from .permissions import permission_workflow_tools
from .tasks import task_launch_workflow_for

logger = logging.getLogger(name=__name__)


class DocumentPropertiesEditAction(WorkflowAction):
    form_fields = {
        'document_label': {
            'label': _(message='Document label'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='The new label to be assigned to the '
                    'document.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }, 'document_description': {
            'label': _(message='Document description'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='The new description to be assigned to the '
                    'document.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }
    }
    label = _(message='Modify document properties')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Document properties'), {
                    'fields': ('document_label', 'document_description')
                },
            ),
        )
        return fieldsets

    def execute(self, context):
        self.document_label = self.kwargs.get('document_label')
        self.document_description = self.kwargs.get(
            'document_description'
        )
        new_label = None
        new_description = None

        if self.document_label:
            new_label = self.render_field(
                field_name='document_label', context=context
            )

        if self.document_description:
            new_description = self.render_field(
                field_name='document_description', context=context
            )

        if new_label or new_description:
            document = context['workflow_instance'].document
            document.label = new_label or document.label
            document.description = new_description or document.description

            model_instance = self.get_model_instance()

            document._event_action_object = model_instance
            document.save()


class DocumentWorkflowLaunchAction(WorkflowAction):
    form_field_widgets = {
        'workflows': {
            'class': 'django.forms.widgets.SelectMultiple', 'kwargs': {
                'attrs': {'class': 'select2'}
            }
        }
    }
    label = _(message='Launch workflows')

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        workflow_template = cls.workflow_template_state.workflow

        workflows_union = Workflow.objects.filter(
            document_types__in=workflow_template.document_types.all()
        ).exclude(pk=workflow_template.pk).distinct()

        fields.update(
            {
                'workflows': {
                    'class': 'mayan.apps.forms.form_fields.ModelFormFieldFilteredModelMultipleChoice',
                    'help_text': _(
                        message='Additional workflows to launch for the document.'
                    ),
                    'kwargs': {
                        'source_queryset': workflows_union,
                        'permission': permission_workflow_tools
                    },
                    'label': _(message='Workflows'),
                    'required': True
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Workflows'), {
                    'fields': ('workflows',)
                },
            ),
        )
        return fieldsets

    def execute(self, context):
        workflows = Workflow.objects.filter(
            pk__in=self.kwargs.get(
                'workflows', ()
            )
        )

        document = context['workflow_instance'].document

        for workflow in workflows:
            task_launch_workflow_for.apply_async(
                kwargs={
                    'document_id': document.pk,
                    'workflow_id': workflow.pk
                }
            )


class HTTPAction(BackendMixinCredentialsOptional, WorkflowAction):
    form_fields = {
        'url': {
            'label': _(message='URL'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(message='The URL to access.'),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        }, 'verify_certificate': {
            'label': _(message='Verify SSL Certificate'),
            'class': 'django.forms.fields.BooleanField',
            'default': DEFAULT_HTTP_ACTION_VERIFY_CERTIFICATES,
            'kwargs': {
                'help_text': _(
                    'Verify or ignore the SSL certificate of the URL.'
                ),
                'required': False
            }
        }, 'method': {
            'label': _(message='Method'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='The HTTP method to use for the request. '
                    'Typical choices are OPTIONS, HEAD, POST, GET, '
                    'PUT, PATCH, DELETE.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        }, 'username': {
            'label': _(message='Username'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Username to use for making the request with '
                    'HTTP Basic Auth. The credential object is available as '
                    '{{ credential }}.'
                ),
                'max_length': 192,
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }, 'password': {
            'label': _(message='Password'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Password to use for making the request with '
                    'HTTP Basic Auth. The credential object is available as '
                    '{{ credential }}.'
                ),
                'max_length': 255,
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }, 'headers': {
            'label': _(message='Headers'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Headers to send with the HTTP request. Must '
                    'be in JSON format. The credential object is available as '
                    '{{ credential }}.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }, 'payload': {
            'label': _(message='Payload'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='A JSON document to include in the request.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': False
            }
        }, 'timeout': {
            'label': _(message='Timeout'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'default': DEFAULT_HTTP_ACTION_TIMEOUT,
            'kwargs': {
                'initial_help_text': _(
                    message='Time in seconds to wait for a response.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        }, 'response_store': {
            'label': _(message='Store response'),
            'class': 'django.forms.fields.BooleanField',
            'default': False,
            'kwargs': {
                'help_text': _(
                    'Store the response in the workflow context.'
                ),
                'required': False
            }
        }, 'response_store_name': {
            'label': _(message='Response variable name'),
            'class': 'django.forms.fields.CharField',
            'default': WORKFLOW_ACTION_HTTP_REQUEST_DEFAULT_RESPONSE_STORE_NAME,
            'kwargs': {
                'help_text': _(
                    'Variable used to store the response in the workflow '
                    'instance context.'
                ),
                'required': False
            }
        }
    }
    label = _(message='Perform an HTTP request')
    previous_dotted_paths = (
        'mayan.apps.document_states.workflow_actions.HTTPPostAction',
    )

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Request'), {
                    'fields': (
                        'url', 'username', 'password', 'headers', 'timeout',
                        'method', 'payload', 'verify_certificate'
                    )
                },
            ),
            (
                _(message='Response'), {
                    'fields': (
                        'response_store', 'response_store_name'
                    )
                },
            ),
        )
        return fieldsets

    def render_field_load(self, field_name, context):
        render_result = self.render_field(
            field_name=field_name, context=context
        ) or '{}'

        try:
            load_result = json.loads(s=render_result, strict=False)
        except Exception as exception:
            raise WorkflowStateActionError(
                _(message='%(field_name)s JSON error: %(exception)s') % {
                    'field_name': field_name, 'exception': exception
                }
            )

        logger.debug('load result: %s', load_result)

        return load_result

    def execute(self, context):
        authentication_context = context.copy()
        model_instance = self.get_model_instance()
        workflow_instance = context['workflow_instance']

        credential = self.get_credential(action_object=model_instance)
        if credential:
            authentication_context['credential'] = credential

        headers = self.render_field_load(
            field_name='headers', context=authentication_context
        )
        method = self.render_field(field_name='method', context=context)
        password = self.render_field(
            field_name='password', context=authentication_context
        )
        payload = self.render_field_load(
            field_name='payload', context=context
        )
        timeout = self.render_field(field_name='timeout', context=context)
        url = self.render_field(field_name='url', context=context)
        username = self.render_field(
            field_name='username', context=authentication_context
        )
        verify = self.kwargs.get(
            'verify_certificate', DEFAULT_HTTP_ACTION_VERIFY_CERTIFICATES
        )

        if '.' in timeout:
            timeout = float(timeout)
        elif timeout:
            timeout = int(timeout)
        else:
            timeout = None

        authentication = None
        if username or password:
            authentication = requests.auth.HTTPBasicAuth(
                password=password, username=username
            )

        response = requests.request(
            auth=authentication, headers=headers, json=payload,
            method=method, timeout=timeout, url=url, verify=verify
        )

        response_store = self.kwargs.get('response_store', False)
        if response_store:
            try:
                json = response.json()
            except requests.exceptions.JSONDecodeError:
                json = {}

            response_variable_name = self.kwargs.get(
                'response_store_name',
                WORKFLOW_ACTION_HTTP_REQUEST_DEFAULT_RESPONSE_STORE_NAME
            )

            try:
                apparent_encoding = response.apparent_encoding
            except TypeError:
                apparent_encoding = None

            response_context = {
                response_variable_name: {
                    'apparent_encoding': apparent_encoding,
                    'encoding': response.encoding,
                    'headers': dict(response.headers),
                    'json': json,
                    'reason': response.reason,
                    'status_code': response.status_code,
                    'text': response.text
                }
            }

            workflow_instance.do_context_update(context=response_context)
