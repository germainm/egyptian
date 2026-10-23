from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import (
    search_model_document, search_model_document_version,
    search_model_document_version_page
)


search_model_document.add_model_field(
    field='versions__version_pages__ocr_content__content',
    label=_(message='Document version OCR')
)


search_model_document_version.add_model_field(
    field='version_pages__ocr_content__content', label=_(message='OCR')
)


search_model_document_version_page.add_model_field(
    field='ocr_content__content', label=_(message='Document version OCR')
)
