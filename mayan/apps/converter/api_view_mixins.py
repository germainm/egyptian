from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import StreamingHttpResponse
from django.views.decorators.cache import patch_cache_control

from rest_framework.exceptions import APIException

from mayan.apps.file_caching.models import CachePartitionFile
from mayan.apps.lock_manager.exceptions import LockError
from mayan.apps.mime_types.classes import MIMETypeBackend

from .api_exceptions import AppImageBusy, AppImageThrottled
from .classes import AppImageErrorImage, ConverterBase
from .exceptions import AppImageError
from .settings import (
    setting_image_cache_time, setting_image_generation_retry_delay,
    setting_image_generation_timeout
)
from .tasks import task_content_object_image_generate
from .utils import IndexedDictionary, factory_file_generator


class APIImageViewMixin:
    def get_content_type(self):
        return ContentType.objects.get_for_model(model=self.obj)

    def get_file_generator(self):
        return factory_file_generator(image_object=self.cache_file)

    def get_serializer(self, *args, **kwargs):
        return None

    def get_serializer_class(self):
        return None

    def get_stream_mime_type(self):
        mime_type_backend = MIMETypeBackend.get_backend_instance()
        with self.cache_file.open() as file_object:
            mime_type, mime_encoding = mime_type_backend.get_mime_type(
                file_object=file_object, mime_type_only=True
            )
            return mime_type

    def retrieve(self, request, **kwargs):
        self.set_object()

        try:
            self.set_cache_file(request=request)
        except LockError:
            raise AppImageBusy(
                wait=setting_image_generation_retry_delay.value
            )
        except AppImageError as exception:
            app_image_error_image = AppImageErrorImage.get(
                name=exception.error_name
            )

            error_image_template_result = app_image_error_image.render(
                context={'details': exception.details}
            )

            detail = {
                'app_image_error_image_template': error_image_template_result
            }

            if exception.details:
                detail['details'] = exception.details

            raise APIException(detail=detail)
        else:
            file_generator = self.get_file_generator()

            content_type = ConverterBase.get_output_content_type()

            if not content_type:
                content_type = self.get_stream_mime_type()

            response = StreamingHttpResponse(
                content_type=content_type, streaming_content=file_generator()
            )

            if '_hash' in request.GET:
                patch_cache_control(
                    max_age=setting_image_cache_time.value,
                    response=response
                )
            return response

    def set_cache_file(self, request):
        query_dict = request.GET

        transformation_dictionary_list = IndexedDictionary(
            dictionary=query_dict
        ).as_dictionary_list()

        maximum_layer_order = request.GET.get('maximum_layer_order') or None
        if maximum_layer_order:
            try:
                maximum_layer_order = int(maximum_layer_order)
            except (TypeError, ValueError):
                maximum_layer_order = None

        transformation_instance_list = IndexedDictionary.from_dictionary_list(
            dictionary_list=transformation_dictionary_list or ()
        ).as_instance_list()

        cache_filename = self.obj.get_image_cache_filename(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=request.user
        )

        try:
            self.cache_file = self.obj.cache_partition.get_file(
                filename=cache_filename
            )
        except CachePartitionFile.DoesNotExist:
            self.set_cache_file_generate(
                maximum_layer_order=maximum_layer_order, request=request,
                transformation_dictionary_list=transformation_dictionary_list
            )

    def set_cache_file_generate(
        self, maximum_layer_order, request, transformation_dictionary_list
    ):
        task = task_content_object_image_generate.apply_async(
            kwargs={
                'content_type_id': self.get_content_type().pk,
                'object_id': self.obj.pk,
                'maximum_layer_order': maximum_layer_order,
                'transformation_dictionary_list': transformation_dictionary_list,
                'user_id': request.user.pk
            }
        )

        kwargs = {'timeout': setting_image_generation_timeout.value}
        if settings.DEBUG:
            kwargs['disable_sync_subtasks'] = False

        try:
            cache_filename = task.get(**kwargs)
        finally:
            task.forget()

        self.cache_file = self.obj.cache_partition.get_file(
            filename=cache_filename
        )

    def set_object(self):
        self.obj = self.get_object()

    def throttled(self, request, wait):
        raise AppImageThrottled(wait=wait)
