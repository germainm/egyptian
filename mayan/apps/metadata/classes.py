from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.module_loading import import_string
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.forms.literals import EMPTY_LABEL


class MetadataTypeParserMetaclass(type):
    _registry = {}

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(
            mcs, name, bases, attrs
        )
        if new_class.__module__ != 'mayan.apps.metadata.classes':
            mcs._registry[
                '{}.{}'.format(new_class.__module__, name)
            ] = new_class

        return new_class


class MetadataTypeValidatorMetaclass(type):
    _registry = {}

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(
            mcs, name, bases, attrs
        )
        if new_class.__module__ != 'mayan.apps.metadata.classes':
            mcs._registry[
                '{}.{}'.format(new_class.__module__, name)
            ] = new_class

        return new_class


class MetadataTypeModuleMixin(AppsModuleLoaderMixin):
    arguments = ()

    @classmethod
    def get_all(cls):
        return cls._registry.values()

    @classmethod
    def get_choices(cls, add_blank=False):
        choices = [
            (
                entry.get_import_path(), entry.get_full_label()
            ) for entry in cls.get_all()
        ]
        choices.sort(
            key=lambda x: x[1]
        )

        if add_blank:
            choices.insert(
                0, (None, EMPTY_LABEL)
            )

        return choices

    @classmethod
    def get_class(cls, dotted_path):
        choices = dict(
            cls.get_choices()
        )

        try:
            choices[dotted_path]
        except KeyError:
            raise ImproperlyConfigured(
                format_lazy(
                    _(message='Invalid `{}` `%s`'), cls._class_label
                ) % dotted_path
            )
        else:
            klass = import_string(dotted_path=dotted_path)
            return klass

    @classmethod
    def get_import_path(cls):
        return cls.__module__ + '.' + cls.__name__

    @classmethod
    def get_full_label(cls):
        arguments_string = ', '.join(cls.arguments)
        if arguments_string:
            arguments_template = '(arguments: {})'.format(arguments_string)
        else:
            arguments_template = ''

        return format_lazy(
            '{label} {arguments_template}'.format(
                arguments_template=arguments_template, label=cls.label
            )
        )

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def execute(self, input_data):
        raise NotImplementedError


class MetadataParser(
    MetadataTypeModuleMixin, metaclass=MetadataTypeParserMetaclass
):
    _class_label = 'MetadataParser'
    _loader_module_name = 'metadata_parsers'

    def parse(self, input_data):
        try:
            return self.execute(input_data)
        except Exception as exception:
            raise ValidationError(message=exception)


class MetadataValidator(
    MetadataTypeModuleMixin, metaclass=MetadataTypeValidatorMetaclass
):
    _class_label = 'MetadataValidator'
    _loader_module_name = 'metadata_validators'

    def validate(self, input_data):
        try:
            self.execute(input_data)
        except Exception as exception:
            raise ValidationError(message=exception)
