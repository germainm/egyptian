import logging
from shutil import copyfileobj

from django.utils.module_loading import import_string

from .literals import COPY_BLOCK_SIZE
from .settings import setting_backend, setting_backend_arguments

logger = logging.getLogger(name=__name__)


class MIMETypeBackend:
    @staticmethod
    def get_backend_instance():
        return import_string(dotted_path=setting_backend.value)(
            **setting_backend_arguments.value
        )

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        return self._init(**kwargs)

    def _init(self, **kwargs):
        pass

    def do_file_object_copy(self, file_object, target_file_object):
        file_object.seek(0)

        if self.copy_length:
            pending_byte_count = self.copy_length

            while pending_byte_count > 0:
                block = file_object.read(
                    min(pending_byte_count, COPY_BLOCK_SIZE)
                )

                if not block:
                    break

                target_file_object.write(block)

                pending_byte_count -= len(block)
        else:
            copyfileobj(fsrc=file_object, fdst=target_file_object)

        file_object.seek(0)
        target_file_object.seek(0)

    def get_mime_type(self, file_object, mime_type_only=False):
        return self._get_mime_type(
            file_object=file_object, mime_type_only=mime_type_only
        )
