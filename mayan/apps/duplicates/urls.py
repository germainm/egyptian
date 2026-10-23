from django.urls import re_path

from .api_views import (
    APIDocumentDuplicateListView, APIDuplicatedDocumentListView
)
from .views.document_views import (
    DocumentDuplicateBackendListView,
    DocumentDuplicateBackendDocumentListView
)
from .views.main_views import (
    DuplicateBackendDocumentListView, DuplicatesBackendListView
)
from .views.tool_views import ScanDuplicatedDocuments

urlpatterns_documents = [
    re_path(
        route=r'^documents/(?P<document_id>\d+)/backends/$',
        name='document_duplicate_backend_list',
        view=DocumentDuplicateBackendListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/backends/(?P<backend_entry_id>\d+)/$',
        name='document_duplicate_backend_document_list',
        view=DocumentDuplicateBackendDocumentListView.as_view()
    )
]

urlpatterns_main = [
    re_path(
        route=r'^documents/duplicate_backends/$',
        name='duplicate_backend_list',
        view=DuplicatesBackendListView.as_view()
    ),
    re_path(
        route=r'^documents/duplicate_backends/(?P<stored_duplicated_backend_id>\d+)/documents/$',
        name='duplicate_backend_document_list',
        view=DuplicateBackendDocumentListView.as_view()
    )
]

urlpatterns_tools = [
    re_path(
        route=r'^documents/duplicated/scan/$',
        name='duplicated_document_scan',
        view=ScanDuplicatedDocuments.as_view()
    )
]

urlpatterns = []
urlpatterns.extend(urlpatterns_documents)
urlpatterns.extend(urlpatterns_main)
urlpatterns.extend(urlpatterns_tools)

api_urls = [
    re_path(
        route=r'^documents/duplicated/$',
        name='duplicateddocument-list',
        view=APIDuplicatedDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/duplicates/$',
        name='documentduplicate-list',
        view=APIDocumentDuplicateListView.as_view()
    )
]
