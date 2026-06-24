import pathlib
from shutil import copyfileobj
import subprocess

from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.exceptions import DependenciesException
from mayan.apps.storage.utils import NamedTemporaryFile

from ..classes import MIMETypeBackend

from .literals import DEFAULT_FILE_PATH


class MIMETypeBackendFileCommand(MIMETypeBackend):
    def _init(self, copy_length=None, file_path=None):
        self.file_path = file_path or DEFAULT_FILE_PATH
        self.copy_length = copy_length

        path = pathlib.Path(self.file_path)

        if not path.is_file():
            raise DependenciesException(
                _(message='file command not installed or not found.')
            )

    def _get_mime_type(self, file_object, mime_type_only):
        with NamedTemporaryFile() as temporary_file_object:
            file_object.seek(0)

            copyfileobj(
                fsrc=file_object, fdst=temporary_file_object,
                length=self.copy_length
            )
            file_object.seek(0)
            temporary_file_object.seek(0)

            cmd = [
                self.file_path, '--brief',
                '--mime-type' if mime_type_only else '--mime',
                temporary_file_object.name
            ]
            completed = subprocess.run(
                args=cmd, capture_output=True, check=False, text=True
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
