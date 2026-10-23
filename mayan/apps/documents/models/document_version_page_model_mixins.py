import logging
from io import BytesIO

from furl import furl

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.classes import ConverterBase
from mayan.apps.converter.exceptions import AppImageError
from mayan.apps.converter.models import LayerTransformation
from mayan.apps.converter.settings import setting_image_generation_timeout
from mayan.apps.converter.transformations import BaseTransformation
from mayan.apps.file_caching.models import CachePartitionFile
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.exceptions import LockError

from ..literals import (
    ERROR_LOG_DOMAIN_NAME,
    IMAGE_ERROR_DOCUMENT_VERSION_PAGE_TRANSFORMATION_ERROR
)

logger = logging.getLogger(name=__name__)


class DocumentVersionPageBusinessLogicMixin:
    @cached_property
    def cache_partition(self):
        partition, created = self.document_version.cache.partitions.get_or_create(
            name=self.cache_partition_name
        )
        return partition

    @property
    def cache_partition_name(self):
        return self.uuid

    def cache_partition_delete(self):
        for partition in self.document_version.cache.partitions.filter(
            name=self.cache_partition_name
        ):
            partition.delete()

    def _do_transformation_list_apply(
        self, converter_instance, transformation_instance_list
    ):
        try:
            for transformation in transformation_instance_list:
                converter_instance.transform(transformation=transformation)
        except Exception as exception:
            logger.error(
                'Error applying transformation to document version page '
                '%d; %s', self.page_number, exception, exc_info=True
            )
            error_log_text = _(
                message='Error applying transformation to page '
                '%(page_number)d; %(exception)s'
            ) % {
                'exception': exception, 'page_number': self.page_number
            }

            self.error_log.create(
                domain_name=ERROR_LOG_DOMAIN_NAME, text=error_log_text
            )
            raise

        return converter_instance.get_page()

    def get_image_cache_filename(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        return self.get_combined_cache_filename(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )

    def generate_image(
        self, _acquire_lock=True, maximum_layer_order=None,
        transformation_instance_list=None, user=None
    ):
        combined_transformation_list = self.get_combined_transformation_list(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )
        combined_cache_filename = self.get_combined_cache_filename(
            _combined_transformation_list=combined_transformation_list
        )

        logger.debug(
            'transformations cache filename: %s', combined_cache_filename
        )

        content_object_lock_name = self.content_object.get_lock_name(
            user=user
        )
        try:
            content_object_lock = LockingBackend.get_backend().acquire_lock(
                name=content_object_lock_name,
                timeout=setting_image_generation_timeout.value * 2
            )
        except Exception:
            raise
        else:
            lock_name = self.get_lock_name(
                _combined_cache_filename=combined_cache_filename
            )
            try:
                if _acquire_lock:
                    lock = LockingBackend.get_backend().acquire_lock(
                        name=lock_name,
                        timeout=setting_image_generation_timeout.value
                    )
            except Exception:
                raise
            else:
                try:
                    try:
                        self.cache_partition.get_file(
                            filename=combined_cache_filename
                        )
                    except CachePartitionFile.DoesNotExist:
                        logger.debug(
                            'transformations cache file "%s" not found, '
                            'generating new image', combined_cache_filename
                        )
                        image = self.get_image(
                            transformation_instance_list=combined_transformation_list
                        )
                        with self.cache_partition.create_file(filename=combined_cache_filename) as file_object:
                            file_object.write(
                                image.getvalue()
                            )
                    else:
                        logger.debug(
                            'transformations cache file "%s" found, '
                            'returning it to caller', combined_cache_filename
                        )

                    return combined_cache_filename
                finally:
                    if _acquire_lock:
                        lock.release()
            finally:
                content_object_lock.release()

    def get_api_image_url(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None, viewname=None, view_kwargs=None,
        _stored_transformation_list=None
    ):
        if not self.content_object:
            return '#'

        transformation_instance_list = transformation_instance_list or ()

        if _stored_transformation_list is None:
            _stored_transformation_list = LayerTransformation.objects.get_for_object(
                as_classes=True, maximum_layer_order=maximum_layer_order,
                obj=self.content_object, user=user
            )

            _stored_transformation_list.extend(
                LayerTransformation.objects.get_for_object(
                    as_classes=True, maximum_layer_order=maximum_layer_order,
                    obj=self, user=user
                )
            )

        transformation_list = list(_stored_transformation_list)

        transformation_list.extend(transformation_instance_list)
        try:
            transformations_hash = BaseTransformation.combine(
                transformations=transformation_list
            )
        except Exception as exception:
            raise AppImageError(
                error_name=IMAGE_ERROR_DOCUMENT_VERSION_PAGE_TRANSFORMATION_ERROR
            ) from exception
        else:
            view_kwargs = view_kwargs or {
                'document_id': self.document_version.document_id,
                'document_version_id': self.document_version_id,
                'document_version_page_id': self.pk
            }

            final_url = furl()
            final_url.path = reverse(
                kwargs=view_kwargs,
                viewname=viewname or 'rest_api:documentversionpage-image'
            )
            final_url.query = BaseTransformation.list_as_query_string(
                transformation_instance_list=transformation_instance_list
            )[1:]
            final_url.args['_hash'] = transformations_hash

            if maximum_layer_order is not None:
                final_url.args['maximum_layer_order'] = maximum_layer_order

            return final_url.tostr()

    def get_combined_cache_filename(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None, _combined_transformation_list=None
    ):
        combined_transformation_list = _combined_transformation_list or self.get_combined_transformation_list(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )

        content_object_cache_filename = self.content_object.get_combined_cache_filename(
            user=user
        )
        return '{}-{}'.format(
            content_object_cache_filename,
            BaseTransformation.combine(
                transformations=combined_transformation_list
            )
        )

    def get_combined_transformation_list(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        result = []

        result.extend(
            LayerTransformation.objects.get_for_object(
                as_classes=True, maximum_layer_order=maximum_layer_order,
                obj=self, user=user
            )
        )

        result.extend(
            transformation_instance_list or []
        )

        return result

    def get_image(self, transformation_instance_list=None):
        cache_filename = '{}-base_image'.format(
            self.content_object.get_combined_cache_filename()
        )
        logger.debug('Page cache filename: %s', cache_filename)

        try:
            cache_file = self.cache_partition.get_file(
                filename=cache_filename
            )
        except CachePartitionFile.DoesNotExist:
            logger.debug('Page cache version "%s" not found', cache_filename)

            try:
                content_object_cache_filename = self.content_object.generate_image(
                    _acquire_lock=False
                )
                content_object_cache_file = self.content_object.cache_partition.get_file(
                    filename=content_object_cache_filename
                )

                with content_object_cache_file.open() as file_object:
                    converter_class = ConverterBase.get_converter_class()
                    converter_instance = converter_class(
                        file_object=file_object
                    )
                    converter_instance.seek_page(page_number=0)

                    page_image = converter_instance.get_page()

                    with self.cache_partition.create_file(filename=cache_filename) as file_object:
                        file_object.write(
                            page_image.getvalue()
                        )

            except LockError:
                raise
            except Exception as exception:
                logger.error(
                    'Error creating document version page cache file '
                    'named "%s"; %s', cache_filename, exception,
                    exc_info=True
                )
                raise
            else:
                if transformation_instance_list:
                    return self._do_transformation_list_apply(
                        converter_instance=converter_instance,
                        transformation_instance_list=transformation_instance_list
                    )
                else:
                    page_image.seek(0)
                    return page_image
        else:
            logger.debug('Page cache version "%s" found', cache_filename)

            if transformation_instance_list:
                with cache_file.open() as file_object:
                    converter_class = ConverterBase.get_converter_class()
                    converter_instance = converter_class(
                        file_object=file_object
                    )

                    converter_instance.seek_page(page_number=0)

                    return self._do_transformation_list_apply(
                        converter_instance=converter_instance,
                        transformation_instance_list=transformation_instance_list
                    )
            else:
                with cache_file.open() as file_object:
                    return BytesIO(
                        file_object.read()
                    )

    def get_label(self):
        return _(
            message='%(document_version)s page %(page_number)d of %(total_pages)d'
        ) % {
            'document_version': str(self.document_version),
            'page_number': self.page_number,
            'total_pages': self.get_pages_last_number() or 1
        }
    get_label.short_description = _(message='Label')

    def get_lock_name(
        self, _combined_cache_filename=None, maximum_layer_order=None,
        transformation_instance_list=None, user=None
    ):
        if _combined_cache_filename:
            combined_cache_filename = _combined_cache_filename
        else:
            combined_cache_filename = self.get_combined_cache_filename(
                maximum_layer_order=maximum_layer_order,
                transformation_instance_list=transformation_instance_list,
                user=user
            )

        return 'document_version_page_generate_image_{}_{}'.format(
            self.pk, combined_cache_filename
        )

    @property
    def is_in_trash(self):
        return self.document_version.is_in_trash

    @property
    def uuid(self):
        return '{}-{}'.format(self.document_version.uuid, self.pk)
