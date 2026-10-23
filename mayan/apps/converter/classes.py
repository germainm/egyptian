import copy
from io import BytesIO
import logging
from pathlib import Path
import shlex
import shutil

import PIL
from PIL import Image, ImageFile
import sh

from django.apps import apps
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.template import loader
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from mayan.apps.file_caching.exceptions import FileCachingException
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.mime_types.classes import MIMETypeBackend
from mayan.apps.navigation.links import Link
from mayan.apps.storage.compressed_files import MsgArchive
from mayan.apps.storage.literals import MSG_MIME_TYPES
from mayan.apps.storage.settings import setting_temporary_directory
from mayan.apps.storage.utils import (
    NamedTemporaryFile, TemporaryDirectory, fs_cleanup
)

from .exceptions import (
    AppImageError, InvalidOfficeFormat, LayerError, OfficeConversionError
)
from .literals import (
    CONVERTER_OFFICE_FILE_MIMETYPES, DEFAULT_LIBREOFFICE_ARGUMENTS,
    DEFAULT_LIBREOFFICE_ENVIRONMENT, DEFAULT_LIBREOFFICE_PATH,
    DEFAULT_PAGE_NUMBER, DEFAULT_PILLOW_FORMAT,
    INTERMEDIATE_FILE_GENERATION_MAXIMUM_ATTEMPTS,
    MAP_PILLOW_FORMAT_TO_MIME_TYPE
)
from .literals import IMAGE_ERROR_BROKEN_FILE
from .settings import (
    get_command_timeout, setting_graphics_backend,
    setting_graphics_backend_arguments, setting_image_generation_timeout,
    setting_load_truncated_images
)

logger = logging.getLogger(name=__name__)


libreoffice_path = setting_graphics_backend_arguments.value.get(
    'libreoffice_path', DEFAULT_LIBREOFFICE_PATH
)


def get_command_libreoffice():
    libreoffice_arguments = setting_graphics_backend_arguments.value.get(
        'libreoffice_arguments', DEFAULT_LIBREOFFICE_ARGUMENTS
    )
    if isinstance(libreoffice_arguments, str):
        libreoffice_arguments = shlex.split(libreoffice_arguments)

    try:
        return sh.Command(path=libreoffice_path).bake(
            '--headless', '--convert-to', 'pdf:writer_pdf_Export',
            *libreoffice_arguments
        )
    except sh.CommandNotFound:
        return None


command_libreoffice = get_command_libreoffice()


class AppImageErrorImage:
    _catch_all = None
    _registry = {}

    @classmethod
    def all(cls):
        return cls._registry.values()

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_catch_all(cls):
        return cls._catch_all

    def __init__(
        self, name, catch_all=False, image_path=None, template_name=None
    ):
        if name in self.__class__._registry:
            raise ImproperlyConfigured(
                '{} already has a entry named `{}`'.format(__class__, name)
            )

        if catch_all and self.__class__._catch_all is not None:
            raise ImproperlyConfigured(
                '{} already has a catch all entry named `{}`'.format(
                    __class__, self.__class__._catch_all.name
                )
            )

        self.name = name
        self.catch_all = catch_all
        self.image_path = image_path
        self.template_name = template_name
        self.template = loader.get_template(template_name=self.template_name)

        self.__class__._registry[name] = self

        if catch_all:
            self.__class__._catch_all = self

    def open(self):
        return staticfiles_storage.open(name=self.image_path, mode='rb')

    def render(self, context=None):
        return self.template.render(context=context)


class ConverterBase:
    @staticmethod
    def get_converter_class():
        return import_string(dotted_path=setting_graphics_backend.value)

    @staticmethod
    def get_output_content_type():
        output_format = setting_graphics_backend_arguments.value.get(
            'pillow_format', DEFAULT_PILLOW_FORMAT
        )

        return MAP_PILLOW_FORMAT_TO_MIME_TYPE.get(output_format)

    @staticmethod
    def is_office_format(mime_type):
        is_office_mime_type = mime_type in CONVERTER_OFFICE_FILE_MIMETYPES
        is_msg_mime_type = mime_type in MSG_MIME_TYPES

        return is_office_mime_type or is_msg_mime_type

    @classmethod
    def get_intermediate_file(
        cls, cache_partition, mime_type, source_file_object_opener,
        filename='intermediate_file'
    ):
        if not cls.is_office_format(mime_type=mime_type):
            return source_file_object_opener()

        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        try:
            cache_file = cache_partition.get_file(filename=filename)
            return cache_file.open()
        except CachePartitionFile.DoesNotExist:
            logger.debug('Intermediate file "%s" not found.', filename)

        lock_name = '{}_generate'.format(
            cache_partition.get_file_lock_name(filename=filename)
        )
        lock_backend = LockingBackend.get_backend()
        lock = lock_backend.acquire_lock(
            name=lock_name, timeout=setting_image_generation_timeout.value
        )

        try:
            for attempt_number in range(INTERMEDIATE_FILE_GENERATION_MAXIMUM_ATTEMPTS):
                try:
                    cache_file = cache_partition.get_file(filename=filename)
                    return cache_file.open()
                except CachePartitionFile.DoesNotExist:
                    logger.debug('Intermediate file "%s" not found.', filename)

                try:
                    with source_file_object_opener() as file_object:
                        converter_class = cls.get_converter_class()
                        converter = converter_class(file_object=file_object)
                        with converter.to_pdf() as pdf_file_object:
                            with cache_partition.create_file(filename=filename) as cache_file_object:
                                shutil.copyfileobj(
                                    fsrc=pdf_file_object, fdst=cache_file_object
                                )
                except InvalidOfficeFormat:
                    return source_file_object_opener()
                except Exception as exception:
                    logger.error(
                        'Error creating intermediate file "%s"; %s.',
                        filename, exception, exc_info=True
                    )
                    try:
                        cache_file = cache_partition.get_file(filename=filename)
                    except CachePartitionFile.DoesNotExist:
                        """Non fatal, ignore."""
                    else:
                        cache_file.delete()

                    raise

            raise FileCachingException(
                'Intermediate file "{}" was evicted immediately after each '
                'of {} generation attempts; the cache maximum size may be '
                'too small.'.format(
                    filename, INTERMEDIATE_FILE_GENERATION_MAXIMUM_ATTEMPTS
                )
            )
        finally:
            lock.release()

    def __init__(self, file_object, mime_type=None):
        ImageFile.LOAD_TRUNCATED_IMAGES = setting_load_truncated_images.value

        self.file_object = file_object
        self.image = None

        if mime_type:
            self.mime_type = mime_type
        else:
            mime_type_backend = MIMETypeBackend.get_backend_instance()
            mime_type_result = mime_type_backend.get_mime_type(
                file_object=file_object, mime_type_only=False
            )
            self.mime_type = mime_type_result[0]
        self.soffice_file = None
        Image.init()
        self.command_libreoffice = command_libreoffice

    def convert(self, page_number=DEFAULT_PAGE_NUMBER):
        self.page_number = page_number

    def get_page(self, output_format=None):
        if not output_format:
            backend_arguments = setting_graphics_backend_arguments.value
            output_format = backend_arguments.get(
                'pillow_format', DEFAULT_PILLOW_FORMAT
            )

        if not self.image:
            self.seek_page(page_number=0)

        image_buffer = BytesIO()
        new_mode = self.image.mode

        if output_format.upper() == 'JPEG':
            new_mode = 'RGB'

        if self.image.mode != new_mode:
            image = self.image.convert(mode=new_mode)
        else:
            image = self.image

        image.save(fp=image_buffer, format=output_format)

        image_buffer.seek(0)

        return image_buffer

    def get_page_count(self):
        try:
            self.soffice_file = self.to_pdf()
        except InvalidOfficeFormat as exception:
            logger.debug('Is not an office format document; %s', exception)

    def seek_page(self, page_number):
        self.file_object.seek(0)

        try:
            self.image = Image.open(fp=self.file_object)
        except IOError:
            self.image = self.convert(page_number=page_number)

            if not self.image:
                error_message = (
                    'Unable to produce an image for the document page. The '
                    'file format is not supported or a required backend '
                    'tool (e.g. pdftoppm from poppler-utils) is not '
                    'available.'
                )
                logger.error(error_message)
                raise AppImageError(
                    details=error_message, error_name=IMAGE_ERROR_BROKEN_FILE
                )
        except PIL.Image.DecompressionBombError as exception:
            error_message = (
                'Unable to seek document page. Increase the '
                'value of the argument "pillow_maximum_image_pixels" in '
                'the CONVERTER_GRAPHICS_BACKEND_ARGUMENTS setting; {}'.format(
                    exception
                )
            )
            logger.error(error_message)
            raise AppImageError(
                details=error_message, error_name=IMAGE_ERROR_BROKEN_FILE
            )
        else:
            try:
                self.image.seek(frame=page_number)
            except Exception as exception:
                error_message = 'Unable to seek document page; {}'.format(
                    exception
                )
                raise AppImageError(
                    details=error_message, error_name=IMAGE_ERROR_BROKEN_FILE
                )
            else:
                try:
                    self.image.load()
                except Exception as exception:
                    error_message = 'Unable to load document page; {}'.format(
                        exception
                    )
                    raise AppImageError(
                        details=error_message,
                        error_name=IMAGE_ERROR_BROKEN_FILE
                    )

    def soffice(self):
        if not self.command_libreoffice:
            raise OfficeConversionError(
                _(message='LibreOffice not installed or not found.')
            )

        with NamedTemporaryFile() as temporary_file_object:
            self.file_object.seek(0)
            shutil.copyfileobj(
                fsrc=self.file_object, fdst=temporary_file_object
            )
            self.file_object.seek(0)
            temporary_file_object.seek(0)

            with TemporaryDirectory() as libreoffice_home_directory:
                path_installation = Path(
                    libreoffice_home_directory, 'LibreOffice_Conversion'
                )
                args = (
                    temporary_file_object.name, '--outdir',
                    setting_temporary_directory.value,
                    '-env:UserInstallation=file://{}'.format(path_installation)
                )

                environment = {'HOME': libreoffice_home_directory}
                environment.update(
                    setting_graphics_backend_arguments.value.get(
                        'libreoffice_environment',
                        DEFAULT_LIBREOFFICE_ENVIRONMENT
                    )
                )

                kwargs = {
                    '_env': environment, '_timeout': get_command_timeout()
                }

                if self.mime_type == 'text/plain':
                    kwargs.update(
                        {'infilter': 'Text (encoded):UTF8,LF,,,'}
                    )

                try:
                    self.command_libreoffice(*args, **kwargs)
                except sh.ErrorReturnCode as exception:
                    temporary_file_object.close()
                    raise OfficeConversionError(exception)
                except sh.TimeoutException as exception:
                    temporary_file_object.close()
                    logger.error(
                        'LibreOffice did not finish before the command '
                        'timeout and was terminated; %s', exception
                    )
                    raise OfficeConversionError(exception)
                except Exception as exception:
                    temporary_file_object.close()
                    logger.error(
                        'Exception launching LibreOffice; %s', exception,
                        exc_info=True
                    )
                    raise



            path_temporary_file = Path(temporary_file_object.name)

            filename = path_temporary_file.stem
            extension = path_temporary_file.suffix

            logger.debug('filename: %s', filename)
            logger.debug('extension: %s', extension)

            converted_file_path = Path(
                setting_temporary_directory.value, path_temporary_file.name
            ).with_suffix('.pdf')
            logger.debug('converted_file_path: %s', converted_file_path)

        temporary_converted_file_object = NamedTemporaryFile()

        try:
            with open(file=converted_file_path, mode='rb') as converted_file_object:
                shutil.copyfileobj(
                    fsrc=converted_file_object,
                    fdst=temporary_converted_file_object
                )
        except Exception:
            temporary_converted_file_object.close()
            raise
        finally:
            fs_cleanup(filename=converted_file_path)

        temporary_converted_file_object.seek(0)
        return temporary_converted_file_object

    def to_pdf(self):
        if self.mime_type in MSG_MIME_TYPES:
            archive = MsgArchive.open(file_object=self.file_object)
            members = archive.members()
            if len(members):
                if 'message.txt' in members:
                    self.file_object = archive.open_member(
                        filename='message.txt'
                    )
                else:
                    self.file_object = archive.open_member(
                        filename=members[0]
                    )

                mime_type_backend = MIMETypeBackend.get_backend_instance()
                mime_type_result = mime_type_backend.get_mime_type(
                    file_object=self.file_object, mime_type_only=True
                )
                self.mime_type = mime_type_result[0]

        if self.mime_type in CONVERTER_OFFICE_FILE_MIMETYPES:
            return self.soffice()
        else:
            raise InvalidOfficeFormat(
                _(message='Not an office file format.')
            )

    def transform(self, transformation):
        if not self.image:
            self.seek_page(page_number=0)

        self.image = transformation.execute_on(image=self.image)

    def transform_many(self, transformations):
        if not self.image:
            self.seek_page(page_number=0)

        for transformation in transformations:
            self.image = transformation.execute_on(image=self.image)


class Layer:
    _registry = {}

    @classmethod
    def all(cls):
        return cls._registry.values()

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_by_value(cls, key, value):
        for name, layer in cls._registry.items():
            if getattr(layer, key) == value:
                return layer

    @classmethod
    def invalidate_cache(cls):
        for layer in cls.all():
            layer.__dict__.pop('stored_layer', None)

    @classmethod
    def update(cls):
        for layer in cls.all():
            layer.stored_layer

    def __init__(
        self, label, name, order, permission_map, default=False,
        empty_results_text=None, icon=None
    ):
        self.default = default
        self.empty_results_text = empty_results_text
        self.label = label
        self.name = name
        self.order = order
        self.permission_map = permission_map
        self.icon = icon

        layer = self.__class__.get_by_value(key='order', value=self.order)

        if layer:
            raise ImproperlyConfigured(
                'Layer "{}" already has order "{}" requested by '
                'layer "{}"'.format(
                    layer.name, order, self.name
                )
            )

        if default:
            layer = self.__class__.get_by_value(key='default', value=True)
            if layer:
                raise ImproperlyConfigured(
                    'Layer "{}" is already the default layer; "{}"'.format(
                        layer.name, self.name
                    )
                )

        self.__class__._registry[name] = self

    def __str__(self):
        return str(self.label)

    def add_transformation_to(
        self, obj, transformation_class, arguments=None, order=None
    ):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )
        content_type = ContentType.objects.get_for_model(model=obj)
        object_layer, created = self.stored_layer.object_layers.get_or_create(
            content_type=content_type, object_id=obj.pk
        )

        if self in transformation_class._layer_transformations:
            return object_layer.transformations.create(
                arguments=arguments or '', order=order,
                name=transformation_class.name
            )
        else:
            raise LayerError(
                'Transformation `{}` not registered for layer `{}`.'.format(
                    transformation_class, self
                )
            )

    def copy_transformations(self, source, targets, delete_existing=False):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        transformations = self.get_transformations_for(obj=source)

        with transaction.atomic():
            for target in targets:
                content_type = ContentType.objects.get_for_model(model=target)
                object_layer, created = self.stored_layer.object_layers.get_or_create(
                    content_type=content_type, object_id=target.pk
                )
                if delete_existing:
                    queryset = object_layer.transformations.all()
                    queryset.delete()

                for transformation in transformations:
                    object_layer.transformations.create(
                        order=transformation.order,
                        name=transformation.name,
                        arguments=transformation.arguments
                    )

    def get_empty_results_text(self):
        if self.empty_results_text:
            return self.empty_results_text
        else:
            return _(
                message='Transformations allow changing the visual appearance '
                'of documents without making permanent changes to the '
                'document file themselves.'
            )

    def get_model_instance(self):
        StoredLayer = apps.get_model(
            app_label='converter', model_name='StoredLayer'
        )
        stored_layer, created = StoredLayer.objects.update_or_create(
            name=self.name, defaults={'order': self.order}
        )

        return stored_layer

    def get_permission(self, action):
        return self.permission_map.get(action, None)

    def get_transformations_for(self, obj, as_classes=False):
        LayerTransformation = apps.get_model(
            app_label='converter', model_name='LayerTransformation'
        )

        return LayerTransformation.objects.get_for_object(
            as_classes=as_classes, obj=obj,
            only_stored_layer=self.stored_layer
        )

    @cached_property
    def stored_layer(self):
        return self.get_model_instance()


class LayerLink(Link):
    def __init__(self, action, layer=None, multi_item=False, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.layer = layer
        self.multi_item = multi_item

    def __repr__(self):
        return '<LayerLink ({} | {})>'.format(
            self.layer, self.action
        )

    def copy(self, layer):
        result = copy.copy(self)
        result.layer = layer

        return result

    def get_icon(self, context):
        if self.action == 'view':
            layer = self.get_layer(context=context)
            if layer and layer.icon:
                return layer.icon

        return super().get_icon(context=context)

    def get_kwargs(self, context):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        if 'content_object' in context:
            content_object_variable = 'content_object'
        else:
            content_object_variable = 'resolved_object'

        content_type = ContentType.objects.get_for_model(
            model=context[content_object_variable]
        )
        layer = self.get_layer(context=context)

        layer_name = layer.name

        result = {
            'app_label': '"{}"'.format(content_type.app_label),
            'model_name': '"{}"'.format(content_type.model),
            'object_id': '{}.pk'.format(content_object_variable),
            'layer_name': '"{}"'.format(layer_name)
        }

        if self.action in ('delete', 'edit') and not self.multi_item:
            result['transformation_id'] = 'object.pk'

        return result

    def get_layer(self, context=None):
        context = context or {}

        if self.layer:
            return self.layer
        elif 'layer' in context:
            return context['layer']
        else:
            layer_name = context.get('layer_name', None)
            if layer_name:
                return Layer.get(name=layer_name)
            else:
                return Layer.get_by_value(key='default', value=True)

    def get_permission_object(self, context):
        try:
            return context['content_object']
        except KeyError:
            try:
                return context['resolved_object']
            except KeyError:
                return None

    def get_permission(self, context):
        layer = self.get_layer(context=context)
        permission = layer.get_permission(action=self.action)

        if permission:
            return permission
        else:
            return None
