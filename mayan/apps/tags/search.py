from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.search import search_model_document
from mayan.apps.dynamic_search.search_models import SearchModel

from .permissions import permission_tag_view


search_model_document.add_model_field(
    field='tags__color', label=_(message='Tag color')
)
search_model_document.add_model_field(
    field='tags__id', help_text=_(message='The database ID of the tag.'),
    label=_(message='Tag ID')
)
search_model_document.add_model_field(
    field='tags__label', label=_(message='Tag label')
)


search_model_tag = SearchModel(
    app_label='tags', model_name='Tag',
    permission=permission_tag_view,
    serializer_path='mayan.apps.tags.serializers.TagSerializer'
)
search_model_tag.add_model_field(field='label')
search_model_tag.add_model_field(field='color')

search_model_tag.add_model_field(
    field='documents__document_type__label', label=_(message='Document type')
)
search_model_tag.add_model_field(
    field='documents__label', label=_(message='Document label')
)
search_model_tag.add_model_field(
    field='documents__description', label=_(message='Document description')
)
search_model_tag.add_model_field(
    field='documents__uuid', label=_(message='Document UUID')
)

search_model_tag.add_model_field(
    field='documents__files__checksum', label=_(message='Document file checksum')
)
search_model_tag.add_model_field(
    field='documents__files__mimetype', label=_(message='Document file MIME type')
)
