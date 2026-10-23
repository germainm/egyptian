from openai import OpenAI

from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.common.utils import flatten_object
from mayan.apps.file_metadata.classes import FileMetadataDriver
from mayan.apps.file_metadata.literals import RESULT_SEPARATOR
from mayan.apps.forms import forms
from mayan.apps.templating.fields import TemplateField
from mayan.apps.templating.template_backends import Template

from .literals import DEFAULT_TIMEOUT


class FileMetadataDriverOpenAIResponseAPI(FileMetadataDriver):
    argument_name_list = (
        'api_key', 'base_url', 'input', 'model', 'organization', 'project',
        'timeout'
    )
    description = _(message='Analyze content using OpenAI\'s Response API.')
    enabled = False
    internal_name = 'openai_response'
    label = _(message='OpenAI Response API driver')
    mime_type_list = ('*',)

    class Form(forms.Form):
        class FormMeta:
            fieldsets = (
                (
                    _(message='Basic'), {
                        'fields': ('enabled', 'arguments')
                    }
                ),
                (
                    _(message='Authentication'), {
                        'fields': ('api_key',)
                    }
                ),
                (
                    _(message='Control'), {
                        'fields': ('organization', 'project', 'model')
                    }
                ),
                (
                    _(message='Prompt'), {
                        'fields': ('input',)
                    }
                ),
                (
                    _(message='Communication'), {
                        'fields': ('base_url', 'timeout',)
                    }
                ),
            )

        base_url = TemplateField(
            initial_help_text=_(
                message='API endpoint base URL. Change this only when using '
                'a compatible non-default endpoint or proxy. The document '
                'file object is available as {{ document_file }}.'
            ), label=_(message='Base URL'), required=False
        )
        api_key = TemplateField(
            initial_help_text=_(
                message='The API key used for authentication. The document '
                'file object is available as {{ document_file }}.'
            ), label=_(message='API Key'), required=True
        )
        input = TemplateField(
            initial_help_text=_(
                message='Text or file content to send to the OpenAI API '
                'for analysis. The document file object is available as '
                '{{ document_file }}.'
            ), label=_(message='Input'), required=False
        )
        model = TemplateField(
            initial_help_text=_(
                message='Identifier of the OpenAI model to use '
                '(for example: gpt-5, gpt-5-nano). The document file object '
                'is available as {{ document_file }}.'
            ), label=_(message='Model'), required=True
        )
        organization = TemplateField(
            initial_help_text=_(
                message='Optional OpenAI organization ID. Used when the '
                'API key is linked to multiple organizations. The document '
                'file object is available as {{ document_file }}.'
            ), label=_(message='Organization'), required=False
        )
        project = TemplateField(
            initial_help_text=_(
                message='Optional OpenAI project ID. Allows scoping '
                'requests to a specific project.  The document file object '
                'is available as {{ document_file }}.'
            ), label=_(message='Project'), required=False
        )
        timeout = TemplateField(
            initial_help_text=_(
                message='Maximum time (in seconds) to wait for a response '
                'from the API before failing.  The document file object is '
                'available as {{ document_file }}.'
            ), label=_(message='Timeout'), required=False
        )

    @classmethod
    def get_argument_values_for_document_file(cls, document_file):
        document_type = document_file.document.document_type

        configuration_instance = document_type.file_metadata_driver_configurations.get(
            stored_driver__internal_name=cls.internal_name
        )

        document_type_arguments = configuration_instance.get_arguments()

        context = {'document_file': document_file}

        argument_values_rendered = {}

        for key, value in document_type_arguments.items():
            template = Template(template_string=value)
            template_result = template.render(context=context)
            argument_values_rendered[key] = template_result

        return argument_values_rendered

    @classmethod
    def get_argument_values_from_settings(cls):
        result = {'timeout': DEFAULT_TIMEOUT}
        setting_arguments = super().get_argument_values_from_settings()

        if setting_arguments:
            result.update(setting_arguments)

        return result

    def __init__(
        self, api_key, input, model, base_url=None, organization=None,
        project=None, timeout=None, **kwargs
    ):
        super().__init__(**kwargs)

        self.api_key = api_key
        self.base_url = base_url or None
        self.input = yaml_load(stream=input)
        self.model = model
        self.organization = organization or None
        self.project = project or None

        if timeout:
            self.timeout = int(timeout)
        else:
            self.timeout = None

    def _process(self, document_file):
        result = {}

        client = OpenAI(
            api_key=self.api_key, base_url=self.base_url,
            organization=self.organization, project=self.project,
            timeout=self.timeout
        )

        response = client.responses.create(
            input=self.input, model=self.model
        )

        dictionary = response.to_dict()
        generator = flatten_object(obj=dictionary, separator=RESULT_SEPARATOR)
        result = dict(generator)

        return result
