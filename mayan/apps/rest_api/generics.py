from django.core.exceptions import ImproperlyConfigured

from rest_framework import generics as rest_framework_generics, status
from rest_framework.response import Response
from rest_framework.settings import api_settings

from mayan.apps.dynamic_search.api_filters import RESTAPISearchFilter

from .api_view_mixins import (
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    SchemaInspectionAPIViewMixin, SerializerExtraContextAPIViewMixin
)
from .filters import MayanObjectPermissionsFilter, MayanSortingFilter
from .permissions import MayanPermission
from .serializers import BlankSerializer


class GenericAPIView(
    CheckQuerysetAPIViewMixin, SchemaInspectionAPIViewMixin,
    QuerySetOverrideCheckAPIViewMixin, rest_framework_generics.GenericAPIView
):
    filter_backends = (MayanObjectPermissionsFilter,)
    permission_classes = (MayanPermission,)
    request_method_real = None

    def initial(self, *args, **kwargs):
        self.request_method_real = self.request.method.upper()
        result = super().initial(*args, **kwargs)
        return result


class CreateAPIView(
    CheckQuerysetAPIViewMixin, InstanceExtraDataAPIViewMixin,
    SchemaInspectionAPIViewMixin, SerializerExtraContextAPIViewMixin,
    QuerySetOverrideCheckAPIViewMixin, rest_framework_generics.CreateAPIView
):
    permission_classes = (MayanPermission,)


class ListAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    SerializerExtraContextAPIViewMixin, SchemaInspectionAPIViewMixin,
    QuerySetOverrideCheckAPIViewMixin, rest_framework_generics.ListAPIView
):
    filter_backends = (
        MayanObjectPermissionsFilter, MayanSortingFilter, RESTAPISearchFilter
    )
    permission_classes = (MayanPermission,)


class ListCreateAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, SerializerExtraContextAPIViewMixin,
    SchemaInspectionAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    rest_framework_generics.ListCreateAPIView
):
    filter_backends = (
        MayanObjectPermissionsFilter, MayanSortingFilter, RESTAPISearchFilter
    )
    permission_classes = (MayanPermission,)


class ObjectActionAPIView(
    SerializerExtraContextAPIViewMixin, GenericAPIView
):
    action_response_status = None
    serializer_class = BlankSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.request_method_real == 'POST':
            context.update(
                {
                    'object': self.get_object()
                }
            )
        return context

    def get_success_headers(self, data):
        try:
            return {
                'Location': str(
                    data[api_settings.URL_FIELD_NAME]
                )
            }
        except (TypeError, KeyError):
            return {}

    def object_action(self, serializer):
        raise ImproperlyConfigured(
            '{cls} class needs to specify the `.perform_action()` '
            'method.'.format(
                cls=self.__class__.__name__
            )
        )

    def post(self, request, *args, **kwargs):
        return self.view_action(request=request, *args, **kwargs)

    def view_action(self, request, *args, **kwargs):
        obj = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(obj, key, value)

        result = self.object_action(
            obj=obj, request=request, serializer=serializer
        )

        if result:
            headers = self.get_success_headers(data=result)
            return Response(
                headers=headers, data=result,
                status=self.action_response_status or status.HTTP_200_OK
            )
        else:
            return Response(
                status=self.action_response_status or status.HTTP_200_OK
            )


class RetrieveAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, SerializerExtraContextAPIViewMixin,
    SchemaInspectionAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    rest_framework_generics.RetrieveAPIView
):
    filter_backends = (MayanObjectPermissionsFilter,)


class RetrieveDestroyAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, SerializerExtraContextAPIViewMixin,
    SchemaInspectionAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    rest_framework_generics.RetrieveDestroyAPIView
):
    filter_backends = (MayanObjectPermissionsFilter,)


class RetrieveUpdateAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, SerializerExtraContextAPIViewMixin,
    SchemaInspectionAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    rest_framework_generics.RetrieveUpdateAPIView
):
    filter_backends = (MayanObjectPermissionsFilter,)


class RetrieveUpdateDestroyAPIView(
    CheckQuerysetAPIViewMixin, DynamicFieldListAPIViewMixin,
    InstanceExtraDataAPIViewMixin, SerializerExtraContextAPIViewMixin,
    SchemaInspectionAPIViewMixin, QuerySetOverrideCheckAPIViewMixin,
    rest_framework_generics.RetrieveUpdateDestroyAPIView
):
    filter_backends = (MayanObjectPermissionsFilter,)
