import ollama

from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.common.utils import flatten_map
from mayan.apps.file_metadata.classes import FileMetadataDriver

from .literals import DEFAULT_TIMEOUT


class FileMetadataDriverOllamaChat(FileMetadataDriver):
    argument_name_list = ('host', 'messages', 'model', 'timeout')
    description = _(message='Analyze content using Ollama.')
    enabled = False
    internal_name = 'ollama_chat'
    label = _(message='Ollama Chat AI driver')
    mime_type_list = ('*',)

    @classmethod
    def get_argument_values_from_settings(cls):
        result = {'timeout': DEFAULT_TIMEOUT}

        setting_arguments = super().get_argument_values_from_settings()

        if setting_arguments:
            result.update(setting_arguments)

        return result

    def __init__(self, host, model, messages, timeout, **kwargs):
        super().__init__(**kwargs)

        self.host = host
        self.messages = yaml_load(stream=messages)
        self.model = model
        self.timeout = int(timeout)

    def _process(self, document_file):
        result = {}

        client = ollama.Client(host=self.host, timeout=self.timeout)

        response = client.chat(model=self.model, messages=self.messages)

        if hasattr(response, 'model_dump'):
            dictionary = response.model_dump()
        else:
            dictionary = response

        flatten_map(dictionary=dictionary, result=result)

        return result
