from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.admin.utils import (
    get_fields_from_path, help_text_for_field, label_for_field
)
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.forms import Form as DjangoForm, ModelForm as DjangoModelForm
from django.forms.models import ModelFormMetaclass
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.utils import resolve_attribute

from .form_fields import (
    CharField, ChoiceField, ModelChoiceField, ModelMultipleChoiceField,
    MultipleChoiceField
)
from .form_mixins import FormMixinDynamicFields, FormMixinFieldsets
from .form_options import DetailFormOption, FilteredSelectionFormOptions
from .form_widgets import (
    DisableableSelectWidget, PlainWidget, RadioSelect, Select, SelectMultiple,
    TextAreaDiv, TextInput
)
from .literals import DEFAULT_CHOICE_FORM_SELECTION_SIZE


class Form(FormMixinFieldsets, DjangoForm):
    pass


class ModelForm(FormMixinFieldsets, DjangoModelForm):
    pass


class ChoiceForm(Form):
    search = CharField(
        label=_(message='Search'), required=False,
        widget=TextInput(
            attrs={
                'autocomplete': 'off',
                'class': 'views-select-search',
                'placeholder': 'Filter list'
            }
        )
    )
    selection = MultipleChoiceField(
        required=False, widget=DisableableSelectWidget()
    )

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop(
            'choices', []
        )
        label = kwargs.pop(
            'label', _(message='Selection')
        )
        help_text = kwargs.pop('help_text', None)
        disabled_choices = kwargs.pop(
            'disabled_choices', ()
        )
        super().__init__(*args, **kwargs)
        self.fields['selection'].choices = choices
        self.fields['selection'].label = label
        self.fields['selection'].help_text = help_text
        self.fields['selection'].widget.disabled_choices = disabled_choices
        self.fields['selection'].widget.attrs.update(
            {
                'class': 'input-hotkey-double-click',
                'size': DEFAULT_CHOICE_FORM_SELECTION_SIZE
            }
        )


class DetailForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.opts = DetailFormOption(
            form=self, kwargs=kwargs, options=getattr(self, 'Meta', None)
        )
        super().__init__(*args, **kwargs)

        for field_index, extra_field in enumerate(iterable=self.opts.extra_fields):
            obj = extra_field.get('object', self.instance)
            field = extra_field.get('field', None)
            func = extra_field.get('func', None)
            label = extra_field.get('label', None)
            help_text = extra_field.get('help_text', None)

            if field:
                if not label:
                    try:
                        fields = get_fields_from_path(model=obj, path=field)
                    except FieldDoesNotExist:
                        attribute = getattr(obj.__class__, field)

                        label = getattr(attribute, 'short_description', field)
                    else:
                        label = label_for_field(
                            model=obj, name=fields[-1].name
                        )

                if not help_text:
                    try:
                        fields = get_fields_from_path(model=obj, path=field)
                    except FieldDoesNotExist:
                        attribute = getattr(obj, field)
                        help_text = getattr(attribute, 'help_text', None)
                    else:
                        help_text = help_text_for_field(
                            model=obj, name=fields[-1].name
                        )

                value = resolve_attribute(attribute=field, obj=obj)

            if func:
                value = func(obj)

            field = field or 'anonymous_field_{}'.format(field_index)

            if isinstance(value, models.query.QuerySet):
                self.fields[field] = ModelMultipleChoiceField(
                    queryset=value, label=label
                )
            else:
                self.fields[field] = CharField(
                    initial=value, label=label, help_text=help_text,
                    widget=extra_field.get('widget', PlainWidget)
                )

        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs.update(
                {'readonly': 'readonly'}
            )


class DynamicForm(FormMixinDynamicFields, Form):
    pass


class DynamicModelForm(FormMixinDynamicFields, ModelForm):
    pass


class FileDisplayForm(Form):
    DIRECTORY = ()
    FILENAME = None

    text = CharField(
        label='',
        widget=TextAreaDiv(
            attrs={
                'class': 'scrollable'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.DIRECTORY or self.FILENAME:
            path_file = Path(
                settings.BASE_DIR, *self.DIRECTORY, self.FILENAME
            )
            with open(file=path_file) as file_object:
                self.fields['text'].initial = file_object.read()


class FilteredSelectionForm(Form):
    def __init__(self, *args, **kwargs):
        opts = FilteredSelectionFormOptions(
            form=self, kwargs=kwargs, options=getattr(self, 'Meta', None)
        )

        if opts.queryset is None:
            if not opts.model:
                raise ImproperlyConfigured(
                    '{} requires a queryset or a model to be specified as '
                    'a meta option or passed during initialization.'.format(
                        self.__class__.__name__
                    )
                )

            queryset = opts.model.objects.all()
        else:
            queryset = opts.queryset

        if opts.allow_multiple:
            extra_kwargs = {}
            field_class = ModelMultipleChoiceField
            widget_class = SelectMultiple
        else:
            extra_kwargs = {'empty_label': None}
            field_class = ModelChoiceField
            widget_class = Select

        if opts.widget_class:
            widget_class = opts.widget_class

        if opts.permission:
            AccessControlList = apps.get_model(
                app_label='acls', model_name='AccessControlList'
            )
            queryset = AccessControlList.objects.restrict_queryset(
                permission=opts.permission, queryset=queryset,
                user=opts.user
            )

        super().__init__(*args, **kwargs)

        self.fields[opts.field_name] = field_class(
            help_text=opts.help_text, label=opts.label,
            queryset=queryset, required=opts.required,
            widget=widget_class(attrs=opts.widget_attributes),
            **extra_kwargs
        )


class RelationshipForm(Form):
    def __init__(self, *args, **kwargs):
        self._event_actor = kwargs.pop('_event_actor')
        super().__init__(*args, **kwargs)

        self.fields['label'] = CharField(
            label=_(message='Label'), required=False,
            widget=TextInput(
                attrs={'readonly': 'readonly'}
            )
        )
        self.fields['relationship_type'] = ChoiceField(
            choices=self.RELATIONSHIP_CHOICES, label=_(message='Relationship'),
            widget=RadioSelect()
        )

        self.sub_object = self.initial.get('sub_object')
        if self.sub_object:
            self.fields['label'].initial = str(self.sub_object)

            self.initial_relationship_type = self.get_relationship_type()

            self.fields['relationship_type'].initial = self.initial_relationship_type

    def get_new_relationship_instance(self):
        related_manager = getattr(
            self.initial.get('object'),
            self.initial['relationship_related_field']
        )
        main_field_name = related_manager.field.name

        return related_manager.model(
            **{
                main_field_name: self.initial.get('object'),
                self.initial['relationship_related_query_field']: self.initial.get('sub_object')
            }
        )

    def get_queryset_relationship(self):
        return getattr(
            self.initial.get('object'),
            self.initial['relationship_related_field']
        ).filter(
            **{
                self.initial['relationship_related_query_field']: self.initial.get('sub_object')
            }
        )

    def get_relationship_instance(self):
        queryset_relationship = self.get_queryset_relationship()
        if queryset_relationship.exists():
            return queryset_relationship.get()
        else:
            return self.get_new_relationship_instance()

    def save(self):
        if self.sub_object:
            if self.cleaned_data['relationship_type'] != self.initial_relationship_type:
                save_method = getattr(
                    self, 'save_relationship_{}'.format(
                        self.cleaned_data['relationship_type']
                    )
                )
                save_method()
