import logging

from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import gettext_lazy as _

from .class_mixins import MixinConditionTemplate

logger = logging.getLogger(name=__name__)


class ExtraDataModelMixin:
    def __init__(self, *args, **kwargs):
        _instance_extra_data = kwargs.pop(
            '_instance_extra_data', {}
        )
        result = super().__init__(*args, **kwargs)
        for key, value in _instance_extra_data.items():
            setattr(self, key, value)

        return result


class MetaClassModelMixinConditionField(ModelBase):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)

        field = cls._meta.get_field('condition')
        field.help_text = cls._condition_help_text

        return cls


class ModelMixinConditionField(
    MixinConditionTemplate, models.Model,
    metaclass=MetaClassModelMixinConditionField
):
    _condition_help_text = _(
        message='The condition that will determine if this object '
        'is executed or not. Conditions that do not return any value, '
        'that return the Python logical None, or an empty string (\'\') '
        'are considered to be logical false, any other value is '
        'considered to be the logical true.'
    )

    condition = models.TextField(
        blank=True, verbose_name=_(message='Condition')
    )

    class Meta:
        abstract = True
