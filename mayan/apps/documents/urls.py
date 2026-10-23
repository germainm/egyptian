from django.urls import re_path

from .api_views.document_api_views import (
    APIDocumentChangeTypeView, APIDocumentDetailView,
    APIDocumentFileActionListView, APIDocumentListView, APIDocumentUploadView
)
from .api_views.document_file_api_views import (
    APIDocumentFileDetailView, APIDocumentFileListView,
    APIDocumentFilePageDetailView, APIDocumentFilePageImageView,
    APIDocumentFilePageListView
)
from .api_views.document_type_api_views import (
    APIDocumentTypeDocumentListView, APIDocumentTypeDetailView,
    APIDocumentTypeListView, APIDocumentTypeQuickLabelDetailView,
    APIDocumentTypeQuickLabelListView
)
from .api_views.document_version_api_views import (
    APIDocumentVersionDetailView, APIDocumentVersionListView,
    APIDocumentVersionModificationBackendListView,
    APIDocumentVersionModificationView, APIDocumentVersionPageDetailView,
    APIDocumentVersionPageImageView, APIDocumentVersionPageListView
)
from .api_views.recently_accessed_document_api_views import (
    APIRecentlyAccessedDocumentListView
)
from .api_views.recently_created_document_api_views import (
    APIRecentlyCreatedDocumentListView
)
from .api_views.trashed_document_api_views import (
    APITrashedDocumentDetailView, APITrashedDocumentImageView,
    APITrashedDocumentListView, APITrashedDocumentRestoreView
)
from .views.document_file_page_views import (
    DocumentFilePageListView, DocumentFilePageNavigationFirst,
    DocumentFilePageNavigationLast, DocumentFilePageNavigationNext,
    DocumentFilePageNavigationPrevious, DocumentFilePageRotateLeftView,
    DocumentFilePageRotateRightView, DocumentFilePageView,
    DocumentFilePageViewResetView, DocumentFilePageZoomInView,
    DocumentFilePageZoomOutView
)
from .views.document_file_views import (
    DocumentFileDeleteView, DocumentFileEditView, DocumentFileIntrospectView,
    DocumentFileListView, DocumentFilePreviewView, DocumentFilePrintFormView,
    DocumentFilePrintPDFView, DocumentFilePrintView,
    DocumentFilePropertiesView,
    DocumentFileTransformationsClearView, DocumentFileTransformationsCloneView
)
from .views.document_type_retention_policy_views import (
    DocumentTypeRetentionPoliciesEditView
)
from .views.document_type_views import (
    DocumentTypeCreateView, DocumentTypeDeleteView,
    DocumentTypeDocumentListView, DocumentTypeEditView,
    DocumentTypeFilenameCreateView, DocumentTypeFilenameDeleteView,
    DocumentTypeFilenameEditView, DocumentTypeFilenameGeneratorEditView,
    DocumentTypeFilenameListView, DocumentTypeListView
)
from .views.document_version_page_views import (
    DocumentVersionPageDeleteView, DocumentVersionPageListRemapView,
    DocumentVersionPageListView, DocumentVersionPageNavigationFirst,
    DocumentVersionPageNavigationLast, DocumentVersionPageNavigationNext,
    DocumentVersionPageNavigationPrevious, DocumentVersionPageRotateLeftView,
    DocumentVersionPageRotateRightView, DocumentVersionPageView,
    DocumentVersionPageViewResetView, DocumentVersionPageZoomInView,
    DocumentVersionPageZoomOutView
)
from .views.document_version_views import (
    DocumentVersionActiveView, DocumentVersionCreateView,
    DocumentVersionDeleteView, DocumentVersionEditView,
    DocumentVersionListView, DocumentVersionModifyView,
    DocumentVersionPreviewView, DocumentVersionPrintFormView,
    DocumentVersionPrintPDFView, DocumentVersionPrintView,
    DocumentVersionTransformationsClearView,
    DocumentVersionTransformationsCloneView
)
from .views.document_views import (
    DocumentListView, DocumentPreviewView, DocumentPropertiesEditView,
    DocumentPropertiesView, DocumentTypeChangeView
)
from .views.recently_accessed_document_views import (
    RecentlyAccessedDocumentListView
)
from .views.recently_created_document_views import (
    RecentCreatedDocumentListView
)
from .views.trashed_document_views import (
    DocumentTrashView, EmptyTrashCanView, TrashedDocumentDeleteView,
    TrashedDocumentListView, TrashedDocumentRestoreView
)

urlpatterns_document_files = [
    re_path(
        route=r'^documents/(?P<document_id>\d+)/files/$',
        name='document_file_list', view=DocumentFileListView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/preview/$',
        name='document_file_preview', view=DocumentFilePreviewView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/delete/$',
        name='document_file_delete',
        view=DocumentFileDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/files/multiple/delete/$',
        name='document_file_multiple_delete',
        view=DocumentFileDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/edit/$',
        name='document_file_edit',
        view=DocumentFileEditView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/introspect/$',
        name='document_file_introspect_single',
        view=DocumentFileIntrospectView.as_view()
    ),
    re_path(
        route=r'^documents/files/multiple/introspect/$',
        name='document_file_introspect_multiple',
        view=DocumentFileIntrospectView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/print/form/$',
        name='document_file_print_form',
        view=DocumentFilePrintFormView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/print/$',
        name='document_file_print_view', view=DocumentFilePrintView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/print/pdf/$',
        name='document_file_print_pdf_view',
        view=DocumentFilePrintPDFView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/properties/$',
        name='document_file_properties',
        view=DocumentFilePropertiesView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/transformations/clear/$',
        name='document_file_transformations_clear',
        view=DocumentFileTransformationsClearView.as_view()
    ),
    re_path(
        route=r'^documents/files/multiple/transformations/clear/$',
        name='document_file_multiple_transformations_clear',
        view=DocumentFileTransformationsClearView.as_view()
    ),
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/transformations/clone/$',
        name='document_file_transformations_clone',
        view=DocumentFileTransformationsCloneView.as_view()
    )
]

urlpatterns_document_file_pages = [
    re_path(
        route=r'^documents/files/(?P<document_file_id>\d+)/pages/$',
        name='document_file_page_list', view=DocumentFilePageListView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/$',
        name='document_file_page_view', view=DocumentFilePageView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/navigation/next/$',
        name='document_file_page_navigation_next',
        view=DocumentFilePageNavigationNext.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/navigation/previous/$',
        name='document_file_page_navigation_previous',
        view=DocumentFilePageNavigationPrevious.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/navigation/first/$',
        name='document_file_page_navigation_first',
        view=DocumentFilePageNavigationFirst.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/navigation/last/$',
        name='document_file_page_navigation_last',
        view=DocumentFilePageNavigationLast.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/zoom/in/$',
        name='document_file_page_zoom_in', view=DocumentFilePageZoomInView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/zoom/out/$',
        name='document_file_page_zoom_out', view=DocumentFilePageZoomOutView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/rotate/left/$',
        name='document_file_page_rotate_left',
        view=DocumentFilePageRotateLeftView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/rotate/right/$',
        name='document_file_page_rotate_right',
        view=DocumentFilePageRotateRightView.as_view()
    ),
    re_path(
        route=r'^documents/files/pages/(?P<document_file_page_id>\d+)/reset/$',
        name='document_file_page_view_reset',
        view=DocumentFilePageViewResetView.as_view()
    )
]

urlpatterns_document_types = [
    re_path(
        route=r'^document_types/$', name='document_type_list',
        view=DocumentTypeListView.as_view()
    ),
    re_path(
        route=r'^document_types/create/$', name='document_type_create',
        view=DocumentTypeCreateView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/delete/$',
        name='document_type_delete', view=DocumentTypeDeleteView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/retention_policies/$',
        name='document_type_retention_policies',
        view=DocumentTypeRetentionPoliciesEditView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/documents/$',
        name='document_type_document_list',
        view=DocumentTypeDocumentListView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/edit/$',
        name='document_type_edit', view=DocumentTypeEditView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/filename_generator/$',
        name='document_type_filename_generator',
        view=DocumentTypeFilenameGeneratorEditView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/filenames/$',
        name='document_type_filename_list',
        view=DocumentTypeFilenameListView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/filenames/create/$',
        name='document_type_filename_create',
        view=DocumentTypeFilenameCreateView.as_view()
    ),
    re_path(
        route=r'^document_types/filenames/(?P<document_type_filename_id>\d+)/delete/$',
        name='document_type_filename_delete',
        view=DocumentTypeFilenameDeleteView.as_view()
    ),
    re_path(
        route=r'^document_types/filenames/(?P<document_type_filename_id>\d+)/edit/$',
        name='document_type_filename_edit',
        view=DocumentTypeFilenameEditView.as_view()
    )
]

urlpatterns_document_version = [
    re_path(
        route=r'^documents/(?P<document_id>\d+)/versions/$',
        name='document_version_list', view=DocumentVersionListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/versions/create/$',
        name='document_version_create',
        view=DocumentVersionCreateView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/active/$',
        name='document_version_active',
        view=DocumentVersionActiveView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/delete/$',
        name='document_version_single_delete',
        view=DocumentVersionDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/edit/$',
        name='document_version_edit',
        view=DocumentVersionEditView.as_view()
    ),
    re_path(
        route=r'^documents/versions/multiple/delete/$',
        name='document_version_multiple_delete',
        view=DocumentVersionDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/modify/$',
        name='document_version_modify',
        view=DocumentVersionModifyView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/preview/$',
        name='document_version_preview',
        view=DocumentVersionPreviewView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/print/form/$',
        name='document_version_print_form',
        view=DocumentVersionPrintFormView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/print/$',
        name='document_version_print_view',
        view=DocumentVersionPrintView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/print/pdf/$',
        name='document_version_print_pdf_view',
        view=DocumentVersionPrintPDFView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/transformations/clear/$',
        name='document_version_transformations_clear',
        view=DocumentVersionTransformationsClearView.as_view()
    ),
    re_path(
        route=r'^documents/versions/multiple/transformations/clear/$',
        name='document_version_multiple_transformations_clear',
        view=DocumentVersionTransformationsClearView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/transformations/clone/$',
        name='document_version_transformations_clone',
        view=DocumentVersionTransformationsCloneView.as_view()
    )
]

urlpatterns_document_version_pages = [
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/pages/$',
        name='document_version_page_list',
        view=DocumentVersionPageListView.as_view()
    ),
    re_path(
        route=r'^documents/versions/pages/(?P<document_version_page_id>\d+)/delete/$',
        name='document_version_page_delete',
        view=DocumentVersionPageDeleteView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_id>\d+)/pages/remap/$',
        name='document_version_page_list_remap',
        view=DocumentVersionPageListRemapView.as_view()
    ),
    re_path(
        route=r'^documents/versions/pages/(?P<document_version_page_id>\d+)/$',
        name='document_version_page_view',
        view=DocumentVersionPageView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/navigation/next/$',
        name='document_version_page_navigation_next',
        view=DocumentVersionPageNavigationNext.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/navigation/previous/$',
        name='document_version_page_navigation_previous',
        view=DocumentVersionPageNavigationPrevious.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/navigation/first/$',
        name='document_version_page_navigation_first',
        view=DocumentVersionPageNavigationFirst.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/navigation/last/$',
        name='document_version_page_navigation_last',
        view=DocumentVersionPageNavigationLast.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/zoom/in/$',
        name='document_version_page_zoom_in', view=DocumentVersionPageZoomInView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/zoom/out/$',
        name='document_version_page_zoom_out', view=DocumentVersionPageZoomOutView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/rotate/left/$',
        name='document_version_page_rotate_left',
        view=DocumentVersionPageRotateLeftView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/rotate/right/$',
        name='document_version_page_rotate_right',
        view=DocumentVersionPageRotateRightView.as_view()
    ),
    re_path(
        route=r'^documents/versions/(?P<document_version_page_id>\d+)/reset/$',
        name='document_version_page_view_reset',
        view=DocumentVersionPageViewResetView.as_view()
    )
]

urlpatterns_documents = [
    re_path(
        route=r'^documents/$', name='document_list',
        view=DocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/recently/accessed/$',
        name='document_recently_accessed_list',
        view=RecentlyAccessedDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/recently/created/$',
        name='document_recently_created_list',
        view=RecentCreatedDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/preview/$',
        name='document_preview', view=DocumentPreviewView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/properties/$',
        name='document_properties', view=DocumentPropertiesView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/properties/edit/$',
        name='document_properties_edit',
        view=DocumentPropertiesEditView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/type/$',
        name='document_type_change',
        view=DocumentTypeChangeView.as_view()
    ),
    re_path(
        route=r'^documents/multiple/type/$',
        name='document_multiple_type_change',
        view=DocumentTypeChangeView.as_view()
    )
]

urlpatterns_trashed_documents = [
    re_path(
        route=r'^documents/(?P<document_id>\d+)/trash/$',
        name='document_trash', view=DocumentTrashView.as_view()
    ),
    re_path(
        route=r'^documents/multiple/trash/$', name='document_multiple_trash',
        view=DocumentTrashView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/$', name='document_list_deleted',
        view=TrashedDocumentListView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/(?P<document_id>\d+)/restore/$',
        name='document_restore', view=TrashedDocumentRestoreView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/multiple/restore/$',
        name='document_multiple_restore',
        view=TrashedDocumentRestoreView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/(?P<document_id>\d+)/delete/$',
        name='document_delete', view=TrashedDocumentDeleteView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/multiple/delete/$',
        name='document_multiple_delete',
        view=TrashedDocumentDeleteView.as_view()
    ),
    re_path(
        route=r'^trash_can/empty/$', name='trash_can_empty',
        view=EmptyTrashCanView.as_view()
    )
]

urlpatterns = []
urlpatterns.extend(urlpatterns_document_files)
urlpatterns.extend(urlpatterns_document_file_pages)
urlpatterns.extend(urlpatterns_document_types)
urlpatterns.extend(urlpatterns_document_version_pages)
urlpatterns.extend(urlpatterns_document_version)
urlpatterns.extend(urlpatterns_documents)
urlpatterns.extend(urlpatterns_trashed_documents)

api_urls_documents = [
    re_path(
        route=r'^document_file_actions/$', name='document-file-action-list',
        view=APIDocumentFileActionListView.as_view()
    ),
    re_path(
        route=r'^documents/$', name='document-list',
        view=APIDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/upload/$', name='document-upload',
        view=APIDocumentUploadView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/$',
        name='document-detail',
        view=APIDocumentDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/type/change/$',
        name='document-change-type', view=APIDocumentChangeTypeView.as_view()
    ),
    re_path(
        route=r'^documents/accessed/$',
        name='recentlyaccesseddocument-list',
        view=APIRecentlyAccessedDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/created/$',
        name='recentlycreateddocument-list',
        view=APIRecentlyCreatedDocumentListView.as_view()
    )
]

api_urls_document_files = [
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/files/$',
        name='documentfile-list',
        view=APIDocumentFileListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/files/(?P<document_file_id>[0-9]+)/$',
        name='documentfile-detail', view=APIDocumentFileDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/files/(?P<document_file_id>[0-9]+)/pages/$',
        name='documentfilepage-list',
        view=APIDocumentFilePageListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/files/(?P<document_file_id>[0-9]+)/pages/(?P<document_file_page_id>[0-9]+)/$',
        name='documentfilepage-detail',
        view=APIDocumentFilePageDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/files/(?P<document_file_id>[0-9]+)/pages/(?P<document_file_page_id>[0-9]+)/image/$',
        name='documentfilepage-image',
        view=APIDocumentFilePageImageView.as_view()
    )
]

api_urls_document_types = [
    re_path(
        route=r'^document_types/$', name='documenttype-list',
        view=APIDocumentTypeListView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>[0-9]+)/$',
        name='documenttype-detail', view=APIDocumentTypeDetailView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>[0-9]+)/documents/$',
        name='documenttype-document-list',
        view=APIDocumentTypeDocumentListView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>[0-9]+)/quick_labels/$',
        name='documenttype-quicklabel-list',
        view=APIDocumentTypeQuickLabelListView.as_view()
    ),
    re_path(
        route=r'^document_types/(?P<document_type_id>[0-9]+)/quick_labels/(?P<document_type_quick_label_id>[0-9]+)/$',
        name='documenttype-quicklabel-detail',
        view=APIDocumentTypeQuickLabelDetailView.as_view()
    )
]

api_urls_document_versions = [
    re_path(
        route=r'^document_version_modification_backends/$',
        name='documentversionmodificationbackend-list',
        view=APIDocumentVersionModificationBackendListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/$',
        name='documentversion-list',
        view=APIDocumentVersionListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/(?P<document_version_id>[0-9]+)/$',
        name='documentversion-detail',
        view=APIDocumentVersionDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/(?P<document_version_id>[0-9]+)/modify/$',
        name='documentversion-modify',
        view=APIDocumentVersionModificationView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/(?P<document_version_id>[0-9]+)/pages/$',
        name='documentversionpage-list',
        view=APIDocumentVersionPageListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/(?P<document_version_id>[0-9]+)/pages/(?P<document_version_page_id>[0-9]+)/$',
        name='documentversionpage-detail',
        view=APIDocumentVersionPageDetailView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>[0-9]+)/versions/(?P<document_version_id>[0-9]+)/pages/(?P<document_version_page_id>[0-9]+)/image/$',
        name='documentversionpage-image',
        view=APIDocumentVersionPageImageView.as_view()
    )
]

api_urls_trashed_documents = [
    re_path(
        route=r'^trashed_documents/$', name='trasheddocument-list',
        view=APITrashedDocumentListView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/(?P<document_id>[0-9]+)/$',
        name='trasheddocument-detail', view=APITrashedDocumentDetailView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/(?P<document_id>[0-9]+)/restore/$',
        name='trasheddocument-restore',
        view=APITrashedDocumentRestoreView.as_view()
    ),
    re_path(
        route=r'^trashed_documents/(?P<document_id>[0-9]+)/image/$',
        name='trasheddocument-image',
        view=APITrashedDocumentImageView.as_view()
    )
]

api_urls = []
api_urls.extend(api_urls_documents)
api_urls.extend(api_urls_document_files)
api_urls.extend(api_urls_document_versions)
api_urls.extend(api_urls_document_types)
api_urls.extend(api_urls_trashed_documents)
