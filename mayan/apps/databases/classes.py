from django.apps import apps
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.utils.translation import gettext_lazy as _

from .utils import help_text_for_field_recursive


class ModelAttribute:
    _class_registry = []
    _model_registry = {}

    @classmethod
    def get_all_choices_for(cls, model):
        result = []

        for klass in cls._class_registry:
            klass_choice_list = klass.get_choices_for(model=model)
            if klass_choice_list:
                result.append(
                    (klass.class_label, klass_choice_list)
                )

        return result

    @classmethod
    def get_choices_for(cls, model):
        klass_choice_list = cls.get_for(model=model)

        return sorted(
            (
                (
                    entry.name, entry.get_display()
                ) for entry in klass_choice_list
            ), key=lambda x: x[1]
        )

    @classmethod
    def get_for(cls, model):
        try:
            return cls._model_registry[cls.class_name][model]
        except KeyError:

            if model.__class__ == models.base.ModelBase:
                return []

            return cls.get_for(
                model=type(model)
            )

    @classmethod
    def register(cls, klass):
        cls._class_registry.append(klass)

    def __init__(self, model, name, label=None, description=None):
        self.model = model
        self.label = label
        self.name = name
        self.description = description
        self._model_registry.setdefault(
            self.class_name, {}
        )
        self._model_registry[self.class_name].setdefault(
            model, []
        )
        self._model_registry[self.class_name][model].append(self)

    def get_display(self, show_name=False):
        if self.description:
            template = '{label} - {description}'
        else:
            template = '{label}'

        label = self.name if show_name else self.label

        result = template.format(label=label, description=self.description)

        return result

    def get_description(self):
        return self.description

    get_description.short_description = _(message='Description')

    def get_label(self):
        return self.label

    get_label.short_description = _(message='Label')

    def get_name(self):
        return self.name

    get_name.help_text = _(message='Example usage of the property.')
    get_name.short_description = _(message='Name')


class ModelField(ModelAttribute):
    class_label = _(message='Model fields')
    class_name = 'field'

    def __init__(self, **kwargs):
        if 'label' in kwargs:
            raise ImproperlyConfigured(
                '`ModelField` and subclasses not longer accept `label` '
                'argument. Ensure the `verbose_name` is set in the model '
                'instead.'
            )

        super().__init__(**kwargs)

        self.do_description_set()
        self.do_label_set()

    def do_description_set(self):
        if not self.description:
            self.description = help_text_for_field_recursive(
                model=self.model, name=self.name
            )

    def do_label_set(self):
        text_model_list = []
        last_model = self.model
        for part in self.name.split(LOOKUP_SEP):
            try:
                field = last_model._meta.get_field(field_name=part)
            except FieldDoesNotExist:
                break
            else:
                verbose_name = str(last_model._meta.verbose_name)
                if last_model != self.model and verbose_name:
                    text_model_list.append(
                        '{}'.format(verbose_name)
                    )

                last_model = field.related_model or field.model

        text_model_list.append(
            str(field.verbose_name)
        )

        self.label = ' > '.join(text_model_list)


class ModelFieldRelated(ModelField):
    class_label = _(message='Model related fields')
    class_name = 'related_field'


class ModelProperty(ModelAttribute):
    class_label = _(message='Model properties')
    class_name = 'property'


class ModelReverseField(ModelField):
    class_label = _(message='Model reverse fields')
    class_name = 'reverse_field'

    def __init__(self, *args, **kwargs):
        super(ModelField, self).__init__(*args, **kwargs)
        self._final_model_verbose_name = None

        if not self.label:
            self.label = self.get_field_attribute(
                attribute='verbose_name_plural'
            )

    def get_field_attribute(self, attribute):
        field = self.model._meta.get_field(field_name=self.name)

        return getattr(field.related_model._meta, attribute)


class ModelQueryFields:
    _registry = {}

    @classmethod
    def get(cls, model):
        try:
            return cls._registry[model]
        except KeyError:
            ModelQueryFields(model=model)
            return cls.get(model=model)

    def __init__(self, model):
        self.model = model
        self.select_related_fields = []
        self.prefetch_related_fields = []
        self.__class__._registry[model] = self

    def add_select_related_field(self, field_name):
        if field_name in self.select_related_fields:
            raise ImproperlyConfigured(
                '"{}" model already has a "{}" query select '
                'related field.'.format(
                    self.model, field_name
                )
            )
        self.select_related_fields.append(field_name)

    def add_prefetch_related_field(self, field_name):
        if field_name in self.prefetch_related_fields:
            raise ImproperlyConfigured(
                '"{}" model already has a "{}" query prefetch '
                'related field.'.format(
                    self.model, field_name
                )
            )
        self.prefetch_related_fields.append(field_name)

    def get_queryset(self, manager_name=None):
        if manager_name:
            manager = getattr(self.model, manager_name)
        else:
            manager = self.model._meta.default_manager

        return self.get_queryset_apply(
            queryset=manager.all()
        )

    def get_queryset_apply(self, queryset):
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(
                *self.prefetch_related_fields
            )

        return queryset


class ModelWrapper:
    @classmethod
    def all(cls):
        class_registry = ModelProperty._model_registry[
            ModelProperty.class_name
        ]

        result = []

        for entry in class_registry.keys():
            instance = cls(model=entry)
            result.append(instance)

        result.sort(
            key=lambda entry: entry.get_name_full()
        )

        return result

    def __init__(self, model):
        self.model = model

        meta = self.model._meta

        self.app_config = meta.app_config
        self.model_name = meta.model_name
        self.verbose_name = meta.verbose_name

    def get_app_label(self):
        return self.app_config.verbose_name

    get_app_label.help_text = _(
        message='Name of the app where the model is defined.'
    )
    get_app_label.short_description = _(message='App')

    def get_name_full(self):
        return '{}.{}'.format(self.app_config.label, self.model_name)

    get_name_full.help_text = _(message='Complete unique name of the model.')
    get_name_full.short_description = _(message='Full name')

    def get_label(self):
        return self.verbose_name

    get_label.help_text = _(message='Human readable name of the model.')
    get_label.short_description = _(message='Label')

    def get_name(self):
        return self.model_name

    get_name.short_description = _(message='Name')


class QuerysetParametersSerializer:
    @staticmethod
    def decompose(_model, _method_name, _manager_name=None, **kwargs):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        _manager_name = _manager_name or _model._meta.default_manager.name

        serialized_kwargs = []
        for name, value in kwargs.items():
            try:
                content_type = ContentType.objects.get_for_model(model=value)
            except AttributeError:
                """The value is not a model instance, pass it as-is."""
                serialized_kwargs.append(
                    {
                        'name': name,
                        'value': value
                    }
                )
            else:
                serialized_kwargs.append(
                    {
                        'content_type_id': content_type.pk,
                        'name': name,
                        'object_id': value.pk
                    }
                )

        return {
            'kwargs': serialized_kwargs,
            'manager_name': _manager_name,
            'method_name': _method_name,
            'model_content_type_id': ContentType.objects.get_for_model(
                model=_model
            ).pk
        }

    @staticmethod
    def rebuild(decomposed_queryset):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        model = ContentType.objects.get_for_id(
            id=decomposed_queryset['model_content_type_id']
        ).model_class()

        queryset = getattr(
            model, decomposed_queryset['manager_name']
        )

        kwargs = {}

        parameter_list = decomposed_queryset.get(
            'kwargs', ()
        )

        for parameter in parameter_list:
            if 'content_type_id' in parameter:
                content_type = ContentType.objects.get_for_id(
                    id=parameter['content_type_id']
                )
                value = content_type.get_object_for_this_type(
                    pk=parameter['object_id']
                )
            else:
                value = parameter['value']

            kwargs[
                parameter['name']
            ] = value

        queryset_method = getattr(
            queryset, decomposed_queryset['method_name']
        )
        return queryset_method(**kwargs)


ModelAttribute.register(klass=ModelProperty)
ModelAttribute.register(klass=ModelField)
ModelAttribute.register(klass=ModelFieldRelated)
ModelAttribute.register(klass=ModelReverseField)
