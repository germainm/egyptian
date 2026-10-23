import logging

from django.contrib import messages
from django.core.files import File
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.literals import DEFAULT_DOCUMENT_FILE_ACTION_NAME
from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_file_new
from mayan.apps.views.generics import SingleObjectListView
from mayan.apps.views.utils import request_is_ajax
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms import NewDocumentFileForm
from ..icons import (
    icon_document_file_source_metadata_list, icon_document_file_upload
)
from ..permissions import permission_document_file_sources_metadata_view

from .base import UploadBaseView

logger = logging.getLogger(name=__name__)


class DocumentFileSourceMetadataList(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_document_file_sources_metadata_view
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_source_metadata_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_document_file_source_metadata_list,
            'no_results_text': _(
                message='This means that the sources system did not record '
                'any information about the creation of the document file.'
            ),
            'no_results_title': _(
                message='No source metadata available for this document file'
            ),
            'object': self.external_object,
            'title': _(
                message='Source metadata for: %(document_file)s'
            ) % {'document_file': self.external_object}
        }

    def get_source_queryset(self):
        return self.external_object.source_metadata.all()


class DocumentFileUploadView(ExternalObjectViewMixin, UploadBaseView):
    document_form = NewDocumentFileForm
    external_object_queryset = Document.valid.all()
    external_object_permission = permission_document_file_new
    external_object_pk_url_kwarg = 'document_id'
    object_permission = permission_document_file_new
    source_link_view_name = 'sources:document_file_upload'
    view_icon = icon_document_file_upload
    view_source_action = 'document_file_upload'

    def dispatch(self, request, *args, **kwargs):
        self.subtemplates_list = []
        result = super().dispatch(request=request, *args, **kwargs)

        try:
            DocumentFile.execute_pre_create_hooks(
                kwargs={
                    'document': self.external_object,
                    'file_object': None,
                    'user': self.request.user
                }
            )
        except Exception as exception:
            messages.error(
                message=_(
                    message='Unable to upload new files for document '
                    '"%(document)s". %(exception)s'
                ) % {
                    'document': self.external_object, 'exception': exception
                }, request=self.request
            )
            return HttpResponseRedirect(
                redirect_to=reverse(
                    kwargs={'document_id': self.external_object.pk},
                    viewname='documents:document_file_list'
                )
            )

        return result

    def forms_valid(self, forms):
        action = self.source.get_action(name='document_file_upload')

        interface_load_kwargs = {
            'document': self.external_object, 'forms': forms,
            'request': self.request, 'view': self
        }

        try:
            source_form = forms.get('source_form')
            form_file_object = None
            if source_form:
                form_file_data = source_form.cleaned_data.get('file')
                if form_file_data:
                    form_file_object = File(file=form_file_data)

            DocumentFile.execute_pre_create_hooks(
                kwargs={
                    'document': self.external_object,
                    'file_object': form_file_object,
                    'user': self.request.user
                }
            )
            action.execute(
                interface_name='View',
                interface_load_kwargs=interface_load_kwargs
            )
        except Exception as exception:
            message = _(
                message='Error executing document file upload task; '
                '%(exception)s'
            ) % {'exception': exception}
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
                raise type(exception)(message)
        else:
            messages.success(
                message=_(
                    message='New document file queued for upload and will be '
                    'available shortly.'
                ), request=self.request
            )

            return HttpResponseRedirect(
                redirect_to=reverse(
                    kwargs={'document_id': self.external_object.pk},
                    viewname='documents:document_file_list'
                )
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'form_action': '{}?{}'.format(
                    reverse(
                        kwargs=self.request.resolver_match.kwargs,
                        viewname=self.request.resolver_match.view_name
                    ), self.request.META['QUERY_STRING']
                ),
                'object': self.external_object,
                'title': _(
                    message='Upload a new file for document "%(document)s" '
                    'from source: %(source)s'
                ) % {
                    'document': self.external_object,
                    'source': self.source.label
                },
                'submit_label': _(message='Upload')
            }
        )
        context.update(
            self.source.get_backend_instance().get_view_context(
                context=context, request=self.request
            )
        )

        return context

    def get_form_extra_kwargs__source_form(self, **kwargs):
        return {'source': self.source}

    def get_initial__document_form(self):
        return {'action': DEFAULT_DOCUMENT_FILE_ACTION_NAME}

    def get_source_link_view_kwargs(self):
        return {
            'document_id': str(self.external_object.pk)
        }
