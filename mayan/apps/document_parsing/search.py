from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import (
    search_model_document, search_model_document_file,
    search_model_document_file_page
)


search_model_document.add_model_field(
    field='files__file_pages__content__content',
    label=_(message='Document file content')
)


search_model_document_file.add_model_field(
    field='file_pages__content__content', label=_(message='Content')
)


search_model_document_file_page.add_model_field(
    field='content__content', label=_(message='Document file page content')
)
