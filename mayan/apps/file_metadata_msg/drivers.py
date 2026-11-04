import logging

from django.utils.translation import gettext_lazy as _

from mayan.apps.file_metadata.classes import FileMetadataDriver
from mayan.apps.storage.literals import MSG_MIME_TYPES
from mayan.apps.storage.outlook import OutlookMessage

logger = logging.getLogger(__name__)


class FileMetadataDriverExtractMSGTool(FileMetadataDriver):
    description = _(
        message='Extracts information from emails saved in Microsoft '
        'Outlook\'s .msg files.'
    )
    dotted_path_previous_list = (
        'mayan.apps.file_metadata.drivers.extract_msg.ExtractMSGToolDriver',
    )
    internal_name = 'extract_msg'
    label = _(message='Extract msg')
    mime_type_list = list(MSG_MIME_TYPES)

    def _process(self, document_file):
        result = {}

        with document_file.open() as file_object:
            message = OutlookMessage(file_object=file_object)
            try:
                if message.cc:
                    result['cc'] = message.cc

                if message.sender:
                    result['sender'] = message.sender

                if message.subject:
                    result['subject'] = message.subject

                if message.to:
                    result['to'] = message.to
            finally:
                message.close()

        logger.debug('message file metadata: %s', result)

        return result
