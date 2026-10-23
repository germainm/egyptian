import io
import logging
import uuid

from PIL import Image
from pypdf import PdfWriter

from django.core.files.base import File
from django.urls import reverse

from .exceptions import AppImageError
from .literals import (
    DEFAULT_PDF_EXPORT_PAGE_SHORT_SIDE_INCHES, PDF_EXPORT_IMAGE_MODES,
    TRANSFORMATION_MARKER, TRANSFORMATION_SEPARATOR
)
from .transformations import BaseTransformation

logger = logging.getLogger(name=__name__)


def transformation_index_sort_key(index):
    try:
        return (0, int(index))
    except (TypeError, ValueError):
        return (1, index)


class IndexedDictionary:
    @classmethod
    def from_dictionary_list(
        cls, dictionary_list, klass=BaseTransformation,
        marker=TRANSFORMATION_MARKER, separator=TRANSFORMATION_SEPARATOR
    ):
        result = {}

        for index, dictionary in enumerate(dictionary_list):
            for key, value in dictionary.items():
                if key == 'name':
                    result_key = '{}{}{}{}'.format(
                        marker, str(index), separator, key
                    )
                    result[result_key] = value
                elif key == 'arguments':
                    for argument_key, argument_value in value.items():
                        result_key = '{}{}{}{}{}{}'.format(
                            marker, str(index), separator,
                            'argument', '__', argument_key
                        )

                        result[result_key] = argument_value

        return cls(
            dictionary=result, klass=klass, marker=marker,
            separator=separator
        )

    def __init__(
        self, dictionary, klass=BaseTransformation,
        marker=TRANSFORMATION_MARKER, separator=TRANSFORMATION_SEPARATOR
    ):
        self.dictionary = dictionary
        self.klass = klass
        self.marker = marker
        self.separator = separator

    def as_dictionary(self):
        result_dictionary = {}

        for key, value in self.dictionary.items():
            if key.startswith(self.marker):
                key = key[len(self.marker):]

                index, part = key.split(self.separator, 1)

                if part == 'name':
                    key = 'name'

                    result_dictionary.setdefault(
                        index, {}
                    )
                    result_dictionary[index].update(
                        {key: value}
                    )

                elif part.startswith('argument'):
                    argument_parts = part.split('__', 1)

                    if len(argument_parts) != 2 or not argument_parts[1]:
                        logger.debug(
                            'Ignoring malformed transformation argument key: '
                            '%s', part
                        )
                        continue

                    key = argument_parts[1]

                    result_dictionary.setdefault(
                        index, {}
                    ).setdefault(
                        'arguments', {}
                    )
                    result_dictionary[index]['arguments'].update(
                        {key: value}
                    )

        return result_dictionary

    def as_dictionary_list(self):
        result_dictionary = self.as_dictionary()
        result_dictionary_list = []

        sorted_keys = sorted(
            result_dictionary, key=transformation_index_sort_key
        )

        for key in sorted_keys:
            result_dictionary_list.append(
                result_dictionary[key]
            )

        return result_dictionary_list

    def as_instance_list(self):
        result_dictionary = self.as_dictionary()
        result_list = []

        sorted_keys = sorted(
            result_dictionary, key=transformation_index_sort_key
        )

        for key in sorted_keys:
            entry = result_dictionary[key]

            name = entry.get('name')
            if not name:
                continue

            try:
                transformation_class = self.klass.get(name=name)
            except KeyError:
                logger.warning(
                    'Ignoring unknown transformation name: %s', name
                )
                continue

            result_list.append(
                transformation_class(
                    **entry.get('arguments', {})
                )
            )

        return result_list


def get_object_image_data(
    obj, maximum_layer_order=None, transformation_instance_list=None,
    user=None, _stored_transformation_list=None
):
    from .classes import AppImageErrorImage

    kwargs = {
        'maximum_layer_order': maximum_layer_order,
        'transformation_instance_list': transformation_instance_list or (),
        'user': user
    }

    if _stored_transformation_list is not None:
        kwargs['_stored_transformation_list'] = _stored_transformation_list

    try:
        url = obj.get_api_image_url(**kwargs)
    except AppImageError as exception:
        app_image_error_image = AppImageErrorImage.get(
            name=exception.error_name
        )

        return {
            'app_image_error_image': app_image_error_image,
            'url': reverse(
                viewname='rest_api:app_image_error-image', kwargs={
                    'app_image_error_name': exception.error_name
                }
            )
        }
    else:
        return {'url': url or ''}


def get_pdf_export_page_resolution(
    image, short_side_inches=DEFAULT_PDF_EXPORT_PAGE_SHORT_SIDE_INCHES
):
    short_side_pixels = min(image.width, image.height)

    if not short_side_pixels or not short_side_inches:
        return None

    return short_side_pixels / short_side_inches


def object_list_export_to_pdf(
    file_object, object_list, maximum_layer_order=None, resolution=None,
    transformation_instance_list=None, user=None
):
    pdf_writer = PdfWriter()
    page_count = 0

    for obj in object_list:
        cache_filename = obj.generate_image(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )
        cache_file = obj.cache_partition.get_file(filename=cache_filename)

        with cache_file.open() as image_file_object:
            image = Image.open(fp=image_file_object)
            image.load()

            if image.mode not in PDF_EXPORT_IMAGE_MODES:
                image = image.convert(mode='RGB')

            if resolution:
                page_resolution = resolution
            else:
                page_resolution = get_pdf_export_page_resolution(image=image)

            keyword_arguments = {'format': 'PDF'}

            if page_resolution:
                keyword_arguments['resolution'] = page_resolution

            with io.BytesIO() as page_file_object:
                image.save(fp=page_file_object, **keyword_arguments)
                page_file_object.seek(0)
                pdf_writer.append(fileobj=page_file_object)

        page_count = page_count + 1

    if page_count:
        pdf_writer.write(stream=file_object)

    return page_count


def factory_file_generator(image_object):
    def file_generator():
        with image_object.open() as file_object:
            while True:
                chunk = file_object.read(File.DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                else:
                    yield chunk

    return file_generator


def model_upload_to(instance, filename):
    return 'converter-asset-{}'.format(
        uuid.uuid4().hex
    )
