from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_version_models import (
    DocumentVersion
)
from mayan.apps.organizations.utils import get_organization_installation_url
from mayan.apps.views.generics import MultipleObjectConfirmActionView

from .icons import icon_document_version_export
from .permissions import permission_document_version_export
from .tasks import task_document_version_export


class DocumentVersionExportView(MultipleObjectConfirmActionView):
    object_permission = permission_document_version_export
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    success_message_single = _(
        message='Document version "%(object)s" export successfully queued.'
    )
    success_message_singular = _(
        message='%(count)d document version export successfully queued.'
    )
    success_message_plural = _(
        message='%(count)d document versions exports successfully queued.'
    )
    title_plural = _(message='Export %(count)d document versions.')
    title_single = _(message='Export document version "%(object)s".')
    title_singular = _(message='Export %(count)d document version.')
    view_icon = icon_document_version_export

    def get_extra_context(self):
        context = {
            'message': _(
                message='The process will be performed in the background. '
                'The exported file will be available in the downloads area.'
            ),
            'submit_label': _(message='Export')
        }

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def object_action(self, form, instance):
        task_document_version_export.apply_async(
            kwargs={
                'document_version_id': instance.pk,
                'organization_installation_url': get_organization_installation_url(
                    request=self.request
                ),
                'user_id': self.request.user.pk
            }
        )
