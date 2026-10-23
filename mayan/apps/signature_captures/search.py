from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import search_model_document
from mayan.apps.dynamic_search.search_models import SearchModel

from .permissions import permission_signature_capture_view


search_model_document.add_model_field(
    field='signature_captures__text', label=_(message='Signature capture text')
)
search_model_document.add_model_field(
    field='signature_captures__user__first_name',
    label=_(message='Signature capture user first name')
)
search_model_document.add_model_field(
    field='signature_captures__user__last_name',
    label=_(message='Signature capture user last name')
)
search_model_document.add_model_field(
    field='signature_captures__user__username',
    label=_(message='Signature capture user username')
)


search_model_signature_capture = SearchModel(
    app_label='signature_captures', model_name='SignatureCapture',
    permission=permission_signature_capture_view,
    serializer_path='mayan.apps.signature_captures.serializers.SignatureCaptureSerializer'
)
search_model_signature_capture.add_model_field(
    field='document__document_type__label', label=_(message='Document type label')
)
search_model_signature_capture.add_model_field(
    field='document__label', label=_(message='Document label')
)
search_model_signature_capture.add_model_field(field='text')
search_model_signature_capture.add_model_field(
    field='user__first_name', label=_(message='User first name')
)
search_model_signature_capture.add_model_field(
    field='user__last_name', label=_(message='User last name')
)
search_model_signature_capture.add_model_field(
    field='user__username', label=_(message='User username')
)
