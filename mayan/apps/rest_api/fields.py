from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from . import serializers


@extend_schema_field(field=OpenApiTypes.OBJECT)
class DynamicSerializerField(serializers.ReadOnlyField):
    serializers = {}

    @classmethod
    def add_serializer(cls, klass, serializer_class):
        if isinstance(klass, str):
            klass = import_string(dotted_path=klass)

        if isinstance(serializer_class, str):
            serializer_class = import_string(dotted_path=serializer_class)

        cls.serializers[klass] = serializer_class

    def to_representation(self, value):
        for klass, serializer_class in self.serializers.items():
            if isinstance(value, klass):
                return serializer_class(
                    context={
                        'format': self.context['format'],
                        'request': self.context['request']
                    }
                ).to_representation(instance=value)

        return _(message='Unable to find serializer class for: %s') % value
