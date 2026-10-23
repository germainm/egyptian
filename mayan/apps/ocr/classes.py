import shutil

from django.utils.encoding import force_str
from django.utils.module_loading import import_string

from mayan.apps.converter.classes import ConverterBase
from mayan.apps.storage.utils import TemporaryFile

from .literals import (
    OCR_IMAGE_FORMAT, OCR_IMAGE_FORMAT_NATIVE_LIST,
    OCR_IMAGE_MODE_NATIVE_LIST, TASK_DOCUMENT_VERSION_PAGE_OCR_TIMEOUT
)
from .settings import setting_ocr_backend, setting_ocr_backend_arguments


class OCRBackendBase:
    @staticmethod
    def get_instance():
        backend_class = import_string(dotted_path=setting_ocr_backend.value)
        backend_instance = backend_class(
            **setting_ocr_backend_arguments.value
        )

        return backend_instance

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_task_time_limit(self):
        return int(
            self.kwargs.get(
                'timeout', TASK_DOCUMENT_VERSION_PAGE_OCR_TIMEOUT
            )
        )

    def execute(self, file_object, language=None, transformations=None):
        self.language = language

        if not transformations:
            transformations = []

        converter_backend = ConverterBase.get_converter_class()
        self.converter = converter_backend(file_object=file_object)

        for transformation in transformations:
            self.converter.transform(transformation=transformation)

        if not self.converter.image:
            self.converter.seek_page(page_number=0)

        source_image = self.converter.image

        mode_is_native = source_image.mode in OCR_IMAGE_MODE_NATIVE_LIST
        format_is_native = source_image.format in OCR_IMAGE_FORMAT_NATIVE_LIST

        encode_required = bool(
            transformations
        ) or not mode_is_native or not format_is_native

        if encode_required:
            if not mode_is_native:
                self.converter.image = source_image.convert(mode='RGB')

            image = self.converter.get_page(output_format=OCR_IMAGE_FORMAT)
        else:
            file_object.seek(0)
            image = file_object

        with TemporaryFile() as temporary_image_file:
            shutil.copyfileobj(fsrc=image, fdst=temporary_image_file)
            temporary_image_file.seek(0)

            ocr_output = self._execute(image_file_object=temporary_image_file)
            return force_str(s=ocr_output)
