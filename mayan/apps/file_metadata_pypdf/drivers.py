from pypdf import PdfReader

from django.utils.translation import gettext_lazy as _

from mayan.apps.file_metadata.classes import FileMetadataDriver


class FileMetadataDriverPyPDF(FileMetadataDriver):
    description = _(message='Read meta information stored in files.')
    internal_name = 'pypdf'
    label = _(message='PyPDF')
    mime_type_list = ('application/pdf',)

    def _process(self, document_file):
        with document_file.open() as file_object:
            with PdfReader(stream=file_object) as reader:
                metadata = reader.metadata

                if metadata is None:
                    return {}

                return {
                    key: metadata[key] for key in metadata
                }
