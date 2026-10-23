import json
import logging

import sh

from django.utils.translation import gettext_lazy as _

from mayan.apps.file_metadata.classes import FileMetadataDriver

from .literals import DEFAULT_EXIF_PATH, DEFAULT_EXIF_TIMEOUT

logger = logging.getLogger(name=__name__)


class FileMetadataDriverEXIF(FileMetadataDriver):
    argument_name_list = ('exiftool_path', 'exiftool_timeout')
    description = _(message='Read meta information stored in files.')
    dotted_path_previous_list = (
        'mayan.apps.file_metadata.drivers.exiftool.EXIFToolDriver',
    )
    internal_name = 'exiftool'
    label = _(message='EXIF Tool')
    mime_type_list = ('*',)

    @classmethod
    def get_argument_values_from_settings(cls):
        result = {
            'exiftool_path': DEFAULT_EXIF_PATH,
            'exiftool_timeout': DEFAULT_EXIF_TIMEOUT
        }

        setting_arguments = super().get_argument_values_from_settings()

        if setting_arguments:
            result.update(setting_arguments)

        return result

    def __init__(self, exiftool_path, exiftool_timeout=None, **kwargs):
        super().__init__(**kwargs)

        if exiftool_timeout is None:
            exiftool_timeout = DEFAULT_EXIF_TIMEOUT

        self.exiftool_timeout = int(exiftool_timeout)

        try:
            command_exiftool = sh.Command(path=exiftool_path)
        except sh.CommandNotFound:
            logger.error(
                'EXIFTool binary not found at: %s', exiftool_path
            )
            self.command_exiftool = None
        else:
            self.command_exiftool = command_exiftool.bake('-j')

    def _process(self, document_file):
        if self.command_exiftool:
            with self.get_document_file_path(document_file=document_file) as path_document_file:
                try:
                    output = self.command_exiftool(
                        path_document_file, _timeout=self.exiftool_timeout
                    )
                except sh.ErrorReturnCode_1 as exception:
                    result = json.loads(s=exception.stdout)[0]

                    if result.get('Error', '') == 'Unknown file type':
                        return result

                    raise
                else:
                    return json.loads(s=output)[0]
        else:
            logger.error(
                'EXIFTool binary not found, not processing document '
                'file: %s', document_file
            )
