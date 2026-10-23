import base64
import logging
import random
from urllib.parse import quote_plus

from mayan.apps.sources.exceptions import SourceActionException

from ..classes import SourceStoredFile

from .stored_file_mixins import (
    SourceBackendMixinStoredFileDeleteInteractive,
    SourceBackendMixinStoredFileDeleteInteractiveNot,
    SourceBackendMixinStoredFileDocumentFileUpload,
    SourceBackendMixinStoredFileDocumentUpload,
    SourceBackendMixinStoredFileImage, SourceBackendMixinStoredFileList
)

logger = logging.getLogger(name=__name__)


class SourceBackendMixinStoredFileSourceBase:
    @classmethod
    def initialize(cls):
        SourceStoredFile.initialize()

    def action_file_get(self, **kwargs):
        source_stored_file = self.get_stored_file(**kwargs)
        yield from (
            {'file': source_stored_file},
        )

    def get_stored_file(self, encoded_filename=None, filename=None):
        identifier = None

        if encoded_filename:
            identifier = encoded_filename
            identifier_name = 'encoded_filename'
        elif filename:
            identifier = filename
            identifier_name = 'filename'

        if not identifier:
            raise SourceActionException(
                'Must provide either `encoded_filename` or `filename`.'
            )

        for stored_file in self.get_stored_file_list():
            if getattr(stored_file, identifier_name) == identifier:
                return stored_file

        raise SourceActionException('Requested file not found.')


class SourceBackendMixinStoredFileInteractive(
    SourceBackendMixinStoredFileDeleteInteractive,
    SourceBackendMixinStoredFileDocumentFileUpload,
    SourceBackendMixinStoredFileDocumentUpload,
    SourceBackendMixinStoredFileImage,
    SourceBackendMixinStoredFileList,
    SourceBackendMixinStoredFileSourceBase
):
    pass


class SourceBackendMixinStoredFileInteractiveNot(
    SourceBackendMixinStoredFileDeleteInteractiveNot,
    SourceBackendMixinStoredFileSourceBase
):
    def get_file_identifier(self):
        file_list_generator = self.get_stored_file_list()

        file_list_generator = list(file_list_generator)

        if file_list_generator:
            choice = random.choice(seq=file_list_generator)

            base64_filename = base64.urlsafe_b64encode(
                s=str(choice).encode('utf8')
            )

            return quote_plus(string=base64_filename)
