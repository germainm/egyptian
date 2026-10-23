from django.forms import ModelChoiceField
from django.forms.fields import *
from django.forms.fields import ChoiceField, MultipleChoiceField
from django.forms.models import ModelMultipleChoiceField

from .field_mixins import (
    FormFieldMixinFilteredQueryset, ModelFieldMixinFilteredQuerySet
)


class FormFieldFilteredModelChoice(
    FormFieldMixinFilteredQueryset, ChoiceField
):
    pass


class FormFieldFilteredModelChoiceMultiple(
    FormFieldMixinFilteredQueryset, MultipleChoiceField
):
    pass


class ModelFormFieldFilteredModelMultipleChoice(
    ModelFieldMixinFilteredQuerySet, ModelMultipleChoiceField
):
    pass
