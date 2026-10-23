from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import search_model_document
from mayan.apps.dynamic_search.search_models import SearchModel

from .permissions import permission_cabinet_view


search_model_cabinet = SearchModel(
    app_label='cabinets', model_name='CabinetSearchResult',
    permission=permission_cabinet_view,
    serializer_path='mayan.apps.cabinets.serializers.CabinetSerializer'
)
search_model_cabinet.add_proxy_model(
    app_label='cabinets', model_name='Cabinet'
)

search_model_cabinet.add_model_field(field='id')
search_model_cabinet.add_model_field(field='label')


search_model_cabinet.add_model_field(
    field='documents__document_type__label', label=_(message='Document type')
)
search_model_cabinet.add_model_field(
    field='documents__label', label=_(message='Document label')
)
search_model_cabinet.add_model_field(
    field='documents__description', label=_(message='Document description')
)
search_model_cabinet.add_model_field(
    field='documents__uuid', label=_(message='Document UUID')
)


search_model_cabinet.add_model_field(
    field='documents__files__checksum', label=_(message='Document file checksum')
)
search_model_cabinet.add_model_field(
    field='documents__files__mimetype', label=_(message='Document file MIME type')
)


search_model_document.add_model_field(
    field='cabinets__id',
    help_text=_(message='The database ID of the cabinet.'),
    label=_(message='Cabinet ID')
)
search_model_document.add_model_field(
    field='cabinets__label', label=_(message='Cabinets')
)
