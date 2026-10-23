import logging

from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.permissions import permission_document_create
from mayan.apps.views.utils import request_is_ajax
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms import NewDocumentForm
from ..icons import icon_document_upload_wizard

from .base import UploadBaseView

logger = logging.getLogger(name=__name__)


class DocumentUploadView(ExternalObjectViewMixin, UploadBaseView):
    document_form = NewDocumentForm
    external_object_class = DocumentType
    external_object_permission = permission_document_create
    object_permission = permission_document_create
    source_link_view_name = 'sources:document_upload'
    view_icon = icon_document_upload_wizard
    view_source_action = 'document_upload'

    def forms_valid(self, forms):
        action = self.source.get_action(name='document_upload')

        interface_load_kwargs = {
            'document_type': self.external_object, 'forms': forms,
            'request': self.request, 'view': self
        }

        try:
            Document.execute_pre_create_hooks(
                kwargs={
                    'document_type': self.external_object,
                    'file_object': None,
                    'user': self.request.user
                }
            )
            action.execute(
                interface_name='View',
                interface_load_kwargs=interface_load_kwargs
            )
        except Exception as exception:
            message = _(
                message='Error processing source document upload; '
                '%(exception)s'
            ) % {
                'exception': exception,
            }
            logger.critical(msg=message, exc_info=True)
            if request_is_ajax(request=self.request):
                return JsonResponse(
                    data={
                        'error': str(message)
                    }, status=500
                )
            else:
                messages.error(
                    message=message.replace('\n', ' '),
                    request=self.request
                )
                raise type(exception)(message) from exception
        else:
            messages.success(
                message=_(
                    message='New document queued for upload and will be '
                    'available shortly.'
                ), request=self.request
            )

            return HttpResponseRedirect(
                redirect_to='{}?{}'.format(
                    reverse(
                        kwargs=self.request.resolver_match.kwargs,
                        viewname=self.request.resolver_match.view_name
                    ), self.request.META['QUERY_STRING']
                ),
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'document_type': self.external_object,
                'title': _(
                    message='Upload a document of type "%(document_type)s" '
                    'from source: %(source)s'
                ) % {
                    'document_type': self.external_object,
                    'source': self.source.label
                }
            }
        )

        context.setdefault(
            'submit_label', _(message='Upload')
        )

        return context

    def get_form_extra_kwargs__document_form(self):
        return {'document_type': self.external_object}

    def get_form_extra_kwargs__source_form(self):
        return {'source': self.source}

    def get_pk_url_kwargs(self):
        return {
            'pk': self.request.GET.get(
                'document_type_id', self.request.POST.get('document_type_id')
            )
        }
