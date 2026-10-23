from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import (
    search_model_document, search_model_document_file
)


search_model_document.add_model_field(
    field='files__file_metadata_drivers__entries__key',
    label=_(message='File metadata key')
)
search_model_document.add_model_field(
    field='files__file_metadata_drivers__entries__value',
    label=_(message='File metadata value')
)


search_model_document_file.add_model_field(
    field='file_metadata_drivers__entries__key',
    label=_(message='File metadata key')
)
search_model_document_file.add_model_field(
    field='file_metadata_drivers__entries__value',
    label=_(message='File metadata value')
)
