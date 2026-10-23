from django.apps import apps
from django.core.exceptions import PermissionDenied

from mayan.apps.documents.column_widgets import ThumbnailWidget
from mayan.apps.navigation.column_widgets import SourceColumnWidget

from .permissions import permission_document_metadata_view


class DocumentMetadataWidget(SourceColumnWidget):
    template_name = 'metadata/document_metadata_widget.html'

    def get_extra_context(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        try:
            AccessControlList.objects.check_access(
                obj=self.value,
                permission=permission_document_metadata_view,
                user=self.request.user
            )
        except PermissionDenied:
            queryset = self.value.metadata.none()
        else:
            queryset = self.value.get_metadata(
                permission=permission_document_metadata_view,
                user=self.request.user
            )

        return {'queryset': queryset}


class SourceColumnWidgetMetadataDocumentThumbnail(ThumbnailWidget):
    def get_document(self):
        return self.value.document
