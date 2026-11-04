from django.utils.translation import gettext_lazy as _

RELATIONSHIP_NO = 'no'
RELATIONSHIP_YES = 'yes'
RELATIONSHIP_CHOICES = (
    (RELATIONSHIP_NO, _(message='No')),
    (RELATIONSHIP_YES, _(message='Yes')),
)

# Section on creating an index template, in the wiki of Egyptian.
URL_WIKI_INDEX_TEMPLATE_CREATE = {
    'en': 'https://wiki.mypalace.ca/en/egyptian/apps/documents/document-indexing#creating-an-index-step-by-step',
    'fr': 'https://wiki.mypalace.ca/fr/egyptian/apps/documents/document-indexing#cr%C3%A9er-un-index-guide-pas-%C3%A0-pas'
}
