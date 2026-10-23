import pathlib
import subprocess

from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.exceptions import DependenciesException
from mayan.apps.storage.utils import NamedTemporaryFile

from ..classes import MIMETypeBackend

from .literals import (
    DEFAULT_COPY_LENGTH, DEFAULT_FILE_PATH, DEFAULT_MIME_TYPE_COMMAND_TIMEOUT
)


class MIMETypeBackendFileCommand(MIMETypeBackend):
    def _init(self, copy_length=None, file_path=None, timeout=None):
        self.file_path = file_path or DEFAULT_FILE_PATH

        if copy_length is None:
            copy_length = DEFAULT_COPY_LENGTH

        self.copy_length = copy_length

        if timeout is None:
            timeout = DEFAULT_MIME_TYPE_COMMAND_TIMEOUT

        self.timeout = timeout

        path = pathlib.Path(self.file_path)

        if not path.is_file():
            raise DependenciesException(
                _(message='file command not installed or not found.')
            )

    def _get_mime_type(self, file_object, mime_type_only):
        with NamedTemporaryFile() as temporary_file_object:
            self.do_file_object_copy(
                file_object=file_object,
                target_file_object=temporary_file_object
            )

            cmd = [
                self.file_path, '--brief',
                '--mime-type' if mime_type_only else '--mime',
                temporary_file_object.name
            ]
            completed = subprocess.run(
                args=cmd, capture_output=True, check=False, text=True,
                timeout=self.timeout
            )
            output = (completed.stdout or '').strip().split(';')

            if output:
                file_mime_type = output[0].strip()
            else:
                file_mime_type = ''

            if mime_type_only:
                file_mime_encoding = 'binary'
            else:
                file_mime_encoding = ''
                if len(output) > 1:
                    charset_part = output[1]
                    if 'charset=' in charset_part:
                        file_mime_encoding = charset_part.split('charset=')[-1].strip()

            return (file_mime_type, file_mime_encoding)
