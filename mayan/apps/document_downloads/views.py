from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.views.document_file_views import (
    DocumentFileListView
)
from mayan.apps.organizations.utils import get_organization_installation_url
from mayan.apps.storage.views.download_views import (
    ViewSingleObjectBackendDownload
)
from mayan.apps.views.generics import MultipleObjectFormActionView
from mayan.apps.views.view_mixins import MultipleExternalObjectViewMixin

from .events import event_document_file_downloaded
from .forms import DocumentDownloadFormSet
from .icons import (
    icon_document_download_multiple, icon_document_file_download_quick
)
from .permissions import permission_document_file_download
from .settings import (
    setting_document_file_download_backend,
    setting_document_file_download_backend_arguments
)
from .tasks import task_document_file_compress


class DocumentDownloadView(
    MultipleExternalObjectViewMixin, MultipleObjectFormActionView
):
    error_message = _(
        message='Unable to queued document "%(instance)s" for file download; '
        '%(exception)s.'
    )
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    form_class = DocumentDownloadFormSet
    object_permission = permission_document_file_download
    source_queryset = DocumentFile.valid.all()
    success_message_plural = _(
        message='%(count)d document files queued for download.'
    )
    success_message_single = _(
        message='Document file "%(object)s" queued for download.'
    )
    success_message_singular = _(
        message='%(count)d document file queued for download.'
    )
    title_plural = _(message='Download files of %(count)d documents')
    title_single = _(message='Download files of document: %(object)s')
    title_singular = _(message='Download files of %(count)d document')
    view_icon = icon_document_download_multiple

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Download'),
            'form_display_mode_table': True,
            'subtitle': _(
                message='The process will be performed in the background. The '
                'document files will be available in the downloads area.'
            )
        }

        if self.object_list.count() == 1:
            document = self.object_list.first().document
            context.update(
                {
                    'object': document
                }
            )
        else:
            document = None

        context.update(
            DocumentFileListView.get_no_results_context(
                document=document, request=self.request
            )
        )

        return context

    def get_initial(self):
        initial = []

        for document_file in self.object_list:
            initial.append(
                {
                    'document': str(document_file.document),
                    'document_file': str(document_file),
                    'document_file_id': document_file.pk
                }
            )

        return initial

    def get_object_list(self):
        return self.get_queryset().filter(
            document_id__in=self.external_object_list.values('pk')
        )

    def object_action(self, instance, form=None):
        pass

    def view_action(self, form=None):
        id_list = [
            form_data['document_file_id'] for form_data in form.cleaned_data if form_data['include']
        ]

        queryset = self.get_object_list().filter(pk__in=id_list)

        task_document_file_compress.apply_async(
            kwargs={
                'id_list': list(
                    queryset.values_list('pk', flat=True)
                ),
                'organization_installation_url': get_organization_installation_url(
                    request=self.request
                ),
                'user_id': self.request.user.pk
            }
        )

        return super().view_action(form=form)


class DocumentFileDownloadView(ViewSingleObjectBackendDownload):
    backend_arguments = setting_document_file_download_backend_arguments.value
    backend_path = setting_document_file_download_backend.value
    download_event_type = event_document_file_downloaded
    object_permission = permission_document_file_download
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_download_quick

    def get_download_event_action_object(self):
        return self.object.document
