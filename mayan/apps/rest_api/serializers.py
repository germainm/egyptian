from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as rest_framework_serializers
from rest_framework.fields import (
    BooleanField, CharField, ChoiceField, DateField, DateTimeField,
    DecimalField, DictField, DurationField, EmailField, Field, FileField,
    FilePathField, FloatField, HiddenField, HStoreField, ImageField,
    IntegerField, IPAddressField, JSONField, ListField, ModelField,
    MultipleChoiceField, ReadOnlyField, RegexField, SerializerMethodField,
    SlugField, TimeField, URLField, UUIDField
)
from rest_framework.relations import (
    HyperlinkedIdentityField, HyperlinkedRelatedField, ManyRelatedField,
    PrimaryKeyRelatedField, RelatedField, SlugRelatedField, StringRelatedField
)
from rest_framework.reverse import reverse
from rest_framework.serializers import (
    HyperlinkedModelSerializer as RESTFrameworkHyperlinkedModelSerializer,
    ModelSerializer as RESTFrameworkModelSerializer
)

from .classes import BatchRequestCollection
from .serializer_mixins import (
    CreateOnlyFieldSerializerMixin, DynamicFieldListSerializerMixin
)


class Serializer(
    DynamicFieldListSerializerMixin, rest_framework_serializers.Serializer
):
    pass


class BatchAPIRequestResponseSerializer(Serializer):
    content = CharField(
        label=_(message='Content'), read_only=True
    )
    data = JSONField(
        label=_(message='Data'), read_only=True
    )
    headers = DictField(
        label=_(message='Headers'), read_only=True
    )
    name = CharField(
        label=_(message='Name'), read_only=True
    )
    status_code = IntegerField(
        label=_(message='Status code'), read_only=True
    )
    requests = JSONField(
        label=_(message='Requests'), style={'base_template': 'textarea.html'},
        write_only=True
    )

    def validate(self, data):
        try:
            BatchRequestCollection(
                request_list=data['requests']
            )
        except Exception as exception:
            raise rest_framework_serializers.ValidationError(
                'Error validating requests; {}'.format(exception)
            )

        return data


class BlankSerializer(Serializer):
    pass


class EndpointSerializer(Serializer):
    label = CharField(
        label=_(message='Label'), read_only=True
    )
    url = SerializerMethodField(
        label=_(message='URL')
    )

    def get_url(self, instance):
        if instance.viewname:
            return reverse(
                kwargs=instance.kwargs, viewname=instance.viewname,
                request=self.context['request'],
                format=self.context['format']
            )


class HyperlinkedModelSerializer(
    CreateOnlyFieldSerializerMixin, DynamicFieldListSerializerMixin,
    RESTFrameworkHyperlinkedModelSerializer
):
    pass


class ModelSerializer(
    CreateOnlyFieldSerializerMixin, DynamicFieldListSerializerMixin,
    RESTFrameworkModelSerializer
):
    pass


class ProjectInformationSerializer(Serializer):
    __author__ = CharField(
        label=_(message='Author'), read_only=True
    )
    __author_email__ = CharField(
        label=_(message='Author email'), read_only=True
    )
    __build__ = CharField(
        label=_(message='Build'), read_only=True
    )
    __build_revision__ = CharField(
        label=_(message='Build revision'), read_only=True
    )
    __build_string__ = CharField(
        label=_(message='Build string'), read_only=True
    )
    __copyright__ = CharField(
        label=_(message='Copyright'), read_only=True
    )
    __description__ = CharField(
        label=_(message='Description'), read_only=True
    )
    __django_version__ = CharField(
        label=_(message='Django version'), read_only=True
    )
    __license__ = CharField(
        label=_(message='License'), read_only=True
    )
    __title__ = CharField(
        label=_(message='Title'), read_only=True
    )
    __version__ = CharField(
        label=_(message='Version'), read_only=True
    )
    __website__ = CharField(
        label=_(message='Website'), read_only=True
    )
