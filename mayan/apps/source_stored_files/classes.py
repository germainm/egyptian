import base64
import binascii
import logging
import pathlib
from urllib.parse import quote_plus, unquote_plus

from furl import furl

from django.apps import apps
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse as rest_framework_reverse

from mayan.apps.common.menus import menu_object
from mayan.apps.converter.classes import AppImageErrorImage, ConverterBase
from mayan.apps.converter.exceptions import AppImageError, InvalidOfficeFormat
from mayan.apps.converter.transformations import TransformationResize
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.sources.literals import STORAGE_NAME_SOURCE_CACHE_FOLDER
from mayan.apps.storage.classes import DefinedStorage
from mayan.apps.views.utils import base64_padding_add

from .column_widgets import StoredFileThumbnailWidget
from .links import link_storage_file_delete, link_source_file_select
from .literals import IMAGE_ERROR_NAME_BASE_ERROR

logger = logging.getLogger(name=__name__)


class SourceStoredFile:
    _initialized = False
    DEFAULT_PREVIEW_MAX_SIZE = 100000000
    IMAGE_ERROR_STAGING_FILE_TOO_LARGE = 'staging_file_too_large'

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            AppImageErrorImage(
                name=SourceStoredFile.IMAGE_ERROR_STAGING_FILE_TOO_LARGE,
                template_name='source_stored_files/errors/staging_file_too_large.html'
            )

            SourceColumn(
                attribute='get_size_display',
                label=_(message='Size'), source=SourceStoredFile,
            )

            SourceColumn(
                label=_(message='Thumbnail'), source=SourceStoredFile,
                widget=StoredFileThumbnailWidget,
                html_extra_classes='text-center'
            )

            menu_object.bind_links(
                links=(link_source_file_select, link_storage_file_delete,),
                sources=(SourceStoredFile,)
            )

            cls._initialized = True

    def __init__(self, source, encoded_filename=None, filename=None):
        self.source = source
        if encoded_filename:
            self.encoded_filename = str(encoded_filename)
            self.do_encoded_filename_decode()
        else:
            if not filename:
                raise ValueError(
                    'Supply either `encoded_filename` or `filename` when '
                    'instantiating a `{}`.'.format(self.__class__.__name__)
                )
            self.filename = filename
            self.encoded_filename = quote_plus(
                base64.urlsafe_b64encode(
                    s=filename.encode('utf8')
                )
            )

        self.do_filename_validate()

    def __str__(self):
        return force_str(s=self.filename)

    @cached_property
    def cache(self):
        Cache = apps.get_model(app_label='file_caching', model_name='Cache')

        return Cache.objects.get(
            defined_storage_name=STORAGE_NAME_SOURCE_CACHE_FOLDER
        )

    @property
    def cache_filename(self):
        return '{}-{}'.format(
            self.source.model_instance_id, self.encoded_filename
        )

    @cached_property
    def cache_partition(self):
        partition, created = self.cache.partitions.get_or_create(
            name='{}'.format(self.source.model_instance_id)
        )
        return partition

    def do_encoded_filename_decode(self):
        filename_encoded_unquoted = unquote_plus(string=self.encoded_filename)
        filename_encoded_unquoted_padded = base64_padding_add(
            value=filename_encoded_unquoted
        )

        try:
            self.filename = base64.b64decode(
                altchars=b'-_', s=filename_encoded_unquoted_padded,
                validate=True
            ).decode('utf8')
        except (binascii.Error, UnicodeDecodeError) as exception:
            raise ValueError(
                'Incorrect `encoded_filename` value.'
            ) from exception

    def delete(self):
        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        try:
            cache_partition_file = self.cache_partition.get_file(
                filename=self.encoded_filename
            )
        except CachePartitionFile.DoesNotExist:
            """Non fatal. Means that the file never cached a preview."""
        else:
            cache_partition_file.delete()

        name = self.get_full_path()
        self.storage_backend_instance.delete(name=name)

    def do_filename_validate(self):
        if not self.filename:
            raise ValueError('Filename cannot be empty.')

        if '\x00' in self.filename:
            raise ValueError(
                'Filename `{}` contains null bytes.'.format(self.filename)
            )

        path = pathlib.Path(self.filename)
        if path.anchor or '..' in path.parts or not path.parts:
            raise ValueError(
                'Filename `{}` must be a non-empty relative path '
                'without traversal components.'.format(self.filename)
            )

    def get_image_cache_filename(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        return self.encoded_filename

    def generate_image(self, transformation_instance_list=None):
        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        cache_filename = self.get_image_cache_filename()

        try:
            self.cache_partition.get_file(filename=cache_filename)
        except CachePartitionFile.DoesNotExist:
            logger.debug('source cache file "%s" not found', cache_filename)

            image = self.get_image(
                transformation_instance_list=transformation_instance_list
            )

            with self.cache_partition.create_file(filename=cache_filename) as file_object:
                file_object.write(
                    image.getvalue()
                )
        else:
            logger.debug('source cache file "%s" found', cache_filename)

        return cache_filename

    def get_api_image_url(
        self, maximum_layer_order=None, transformation_instance_list=None,
        request=None, user=None
    ):
        if self.get_size() > self.get_source_preview_max_size():
            raise AppImageError(
                error_name=SourceStoredFile.IMAGE_ERROR_STAGING_FILE_TOO_LARGE
            )

        final_url = furl()
        final_url.args = {'encoded_filename': self.encoded_filename}
        final_url.path = rest_framework_reverse(
            'rest_api:source_action-execute', kwargs={
                'action_name': 'file_image',
                'source_id': self.source.model_instance_id
            }, request=request
        )

        return final_url.tostr()

    def get_combined_transformation_list(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        result = [
            TransformationResize(
                height=self.source.kwargs.get('preview_height'),
                width=self.source.kwargs['preview_width']
            )
        ]

        result.extend(
            transformation_instance_list or []
        )

        return result

    def get_full_path(self):
        return self.filename

    def get_image(self, transformation_instance_list=None):
        if self.get_size() > self.get_source_preview_max_size():
            raise AppImageError(
                error_name=SourceStoredFile.IMAGE_ERROR_STAGING_FILE_TOO_LARGE
            )

        try:
            with self.open(mode='rb') as file_object:
                converter = ConverterBase.get_converter_class()(
                    file_object=file_object
                )

                try:
                    with converter.to_pdf() as pdf_file_object:
                        image_converter = ConverterBase.get_converter_class()(
                            file_object=pdf_file_object
                        )
                        page_image = image_converter.get_page()
                except InvalidOfficeFormat:
                    page_image = converter.get_page()
        except Exception as exception:
            logger.error(
                'Error getting staging file image for file "%s"; %s',
                self.get_full_path(), exception
            )
            raise AppImageError(
                details=str(exception), error_name=IMAGE_ERROR_NAME_BASE_ERROR
            ) from exception
        else:
            return page_image

    def get_size(self):
        return self.storage_backend_instance.size(
            name=self.get_full_path()
        )

    def get_size_display(self):
        return filesizeformat(
            bytes_=self.get_size()
        )

    def get_source_preview_max_size(self):
        return self.source.kwargs.get(
            'preview_max_size', SourceStoredFile.DEFAULT_PREVIEW_MAX_SIZE
        )

    @cached_property
    def image_cache_storage(self):
        return DefinedStorage.get(
            name=STORAGE_NAME_SOURCE_CACHE_FOLDER
        ).get_storage_instance()

    def open(self, mode=None):
        name = self.get_full_path()
        return self.storage_backend_instance.open(mode=mode, name=name)

    @cached_property
    def storage_backend_instance(self):
        return self.source.get_storage_backend_instance()
