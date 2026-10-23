from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import (
    search_model_document, search_model_document_file
)


search_model_document.add_model_field(
    field='files__source_metadata__key', label=_(
        message='Source metadata key'
    )
)
search_model_document.add_model_field(
    field='files__source_metadata__value', label=_(
        message='Source metadata value'
    )
)


search_model_document_file.add_model_field(
    field='source_metadata__key', label=_(message='Source metadata key')
)
search_model_document_file.add_model_field(
    field='source_metadata__value', label=_(message='Source metadata value')
)
