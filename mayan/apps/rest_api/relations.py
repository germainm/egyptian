from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.relations import HyperlinkedIdentityField

from mayan.apps.common.utils import resolve_attribute

from . import serializers
from .field_mixins import (
    AutoHelpTextLabelFieldMixin, FilteredRelatedFieldMixin
)


@extend_schema_field(field=OpenApiTypes.INT)
class FilteredPrimaryKeyRelatedField(
    AutoHelpTextLabelFieldMixin, FilteredRelatedFieldMixin,
    serializers.PrimaryKeyRelatedField
):
    pass


class FilteredSimplePrimaryKeyRelatedField(
    AutoHelpTextLabelFieldMixin, FilteredRelatedFieldMixin,
    serializers.RelatedField
):
    default_error_messages = {
        'does_not_exist': _(
            message='Invalid pk "{pk_value}" - object does not exist.'
        ),
        'incorrect_type': _(
            message='Incorrect type. Expected pk value, received {data_type}.'
        ),
        'required': _(message='This field is required.')
    }

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', 'pk')
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        kwargs = {
            self.pk_field: data
        }

        queryset = self.get_queryset()
        try:
            return getattr(
                queryset.get(**kwargs), self.pk_field
            )
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail(
                'incorrect_type', data_type=type(data).__name__
            )

    def to_representation(self, value):
        return getattr(value, self.pk_field)


class MultiKwargHyperlinkedIdentityField(HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        self.view_kwargs = kwargs.pop(
            'view_kwargs', []
        )
        super().__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        kwargs = {}
        for entry in self.view_kwargs:
            kwargs[
                entry['lookup_url_kwarg']
            ] = resolve_attribute(
                attribute=entry['lookup_field'], obj=obj
            )

        return self.reverse(
            format=format, kwargs=kwargs, request=request, viewname=view_name
        )
