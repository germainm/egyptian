import pathlib
import subprocess

from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.exceptions import DependenciesException
from mayan.apps.storage.utils import NamedTemporaryFile

from ..classes import MIMETypeBackend

from .literals import (
    DEFAULT_COPY_LENGTH, DEFAULT_MIME_TYPE_COMMAND_TIMEOUT,
    DEFAULT_MIMETYPE_PATH
)


class MIMETypeBackendPerlFileMIMEInfo(MIMETypeBackend):
    def _init(self, copy_length=None, mimetype_path=None, timeout=None):
        self.mimetype_path = mimetype_path or DEFAULT_MIMETYPE_PATH

        if copy_length is None:
            copy_length = DEFAULT_COPY_LENGTH

        self.copy_length = copy_length

        if timeout is None:
            timeout = DEFAULT_MIME_TYPE_COMMAND_TIMEOUT

        self.timeout = timeout

        path = pathlib.Path(self.mimetype_path)

        if not path.is_file():
            raise DependenciesException(
                _(message='mimetype command not installed or not found.')
            )

    def _get_mime_type(self, file_object, mime_type_only):
        with NamedTemporaryFile() as temporary_file_object:
            self.do_file_object_copy(
                file_object=file_object,
                target_file_object=temporary_file_object
            )

            cmd = [
                self.mimetype_path, '--magic-only', temporary_file_object.name
            ]
            completed = subprocess.run(
                args=cmd, capture_output=True, check=False, text=True,
                timeout=self.timeout
            )

            file_mime_type = self.do_output_parse(
                output=completed.stdout
            )

            return (file_mime_type, 'binary')

    def do_output_parse(self, output):
        parts_raw = (output or '')
        parts_striped = parts_raw.strip()
        parts_split = parts_striped.rsplit(maxsplit=1)

        if len(parts_split) == 2:
            return parts_split[1]
        else:
            return ''
