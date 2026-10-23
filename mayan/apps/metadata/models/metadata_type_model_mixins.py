from django.core.exceptions import ImproperlyConfigured, ValidationError

from mayan.apps.common.serialization import yaml_load
from mayan.apps.common.utils import comma_splitter
from mayan.apps.templating.template_backends import Template

from ..classes import MetadataParser, MetadataValidator


class MetadataTypeBusinessLogicMixin:
    def get_default_value(self):
        template = Template(template_string=self.default)
        return template.render()

    def get_lookup_values(self):
        template = Template(
            context_entry_name_list=('groups', 'users'),
            template_string=self.lookup
        )

        template_result = template.render()

        return comma_splitter(string=template_result)

    def get_parser_instance(self):
        try:
            parser_class = MetadataParser.get_class(dotted_path=self.parser)
        except ImproperlyConfigured as exception:
            raise ValidationError(message=exception)

        stream = self.parser_arguments or '{}'
        parser_arguments = yaml_load(stream=stream)
        parser = parser_class(**parser_arguments)
        return parser

    def get_required_for(self, document_type):
        queryset = document_type.metadata.filter(
            required=True, metadata_type=self
        )

        return queryset.exists()

    def get_validator_instance(self):
        try:
            validator_class = MetadataValidator.get_class(
                dotted_path=self.validation
            )
        except ImproperlyConfigured as exception:
            raise ValidationError(message=exception)

        stream = self.validation_arguments or '{}'
        validator_arguments = yaml_load(stream=stream)
        validator = validator_class(**validator_arguments)

        return validator
