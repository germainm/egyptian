import io
import logging

from PIL import Image
from furl import furl

from django.apps import apps
from django.db.models import Max
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.file_caching.models import CachePartitionFile
from mayan.apps.storage.hashing import chunk_hash_file_object

from .literals import STORAGE_NAME_ASSETS_CACHE
from .transformations import BaseTransformation

logger = logging.getLogger(name=__name__)


class AssetBusinessLogicMixin:
    @cached_property
    def cache(self):
        Cache = apps.get_model(app_label='file_caching', model_name='Cache')

        return Cache.objects.get(
            defined_storage_name=STORAGE_NAME_ASSETS_CACHE
        )

    @cached_property
    def cache_partition(self):
        partition, created = self.cache.partitions.get_or_create(
            name='{}'.format(self.pk)
        )
        return partition

    def get_image_cache_filename(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        return '{}'.format(
            self.get_hash()
        )

    def generate_image(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        cache_filename = self.get_image_cache_filename()

        try:
            self.cache_partition.get_file(filename=cache_filename)
        except CachePartitionFile.DoesNotExist:
            logger.debug('asset cache file "%s" not found', cache_filename)

            image = self.get_image()
            with io.BytesIO() as image_buffer:
                image.save(image_buffer, format='PNG')

                with self.cache_partition.create_file(filename=cache_filename) as file_object:
                    file_object.write(
                        image_buffer.getvalue()
                    )
        else:
            logger.debug('asset cache file "%s" found', cache_filename)

        return cache_filename

    def get_api_image_url(self, *args, **kwargs):
        final_url = furl()
        final_url.args = kwargs
        final_url.path = reverse(
            viewname='rest_api:asset-image',
            kwargs={'asset_id': self.pk}
        )
        final_url.args['_hash'] = self.get_hash()

        return final_url.tostr()

    def get_hash(self):
        if not self.file_hash:
            self.hash_update()

        return self.file_hash

    def hash_update(self, save=True):
        with self.open() as file_object:
            hash_object = chunk_hash_file_object(file_object=file_object)

        self.file_hash = hash_object.hexdigest()

        if save and self.pk:
            queryset = self.__class__.objects.filter(pk=self.pk)
            queryset.update(file_hash=self.file_hash)

        return self.file_hash

    def get_image(self):
        with self.open() as file_object:
            image = Image.open(fp=file_object)
            image.load()

            if image.mode != 'RGBA':
                image.putalpha(alpha=255)

        return image

    def open(self):
        name = self.file.name
        self.file.close()
        return self.file.storage.open(name=name)


class ObjectLayerBusinessLogicMixin:
    def get_next_order(self):
        last_order = self.transformations.aggregate(
            Max('order')
        )['order__max']

        if last_order is not None:
            return last_order + 1
        else:
            return 0


class LayerTransformationBusinessLogicMixin:
    def get_arguments_column(self):
        try:
            arguments = yaml_load(stream=self.arguments or '{}')
        except Exception:
            arguments = {
                'error': _(message='Badly formatted arguments YAML')
            }

        result = []
        for key, value in arguments.items():
            result.append(
                '{}: {}'.format(key, value)
            )

        return ', '.join(result)

    get_arguments_column.short_description = _(message='Arguments')

    def get_transformation_class(self):
        return BaseTransformation.get(name=self.name)
