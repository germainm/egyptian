from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.forms.document_type_forms import (
    DocumentTypeFilteredSelectForm
)
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.views.generics import (
    FormView, SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_document_type_file_metadata_driver_configuration_edit,
    icon_document_type_file_metadata_driver_configuration_list,
    icon_document_type_file_metadata_submit, icon_file_metadata_driver
)
from ..models import DocumentTypeDriverConfiguration
from ..permissions import (
    permission_document_type_file_metadata_setup,
    permission_file_metadata_submit
)

from .view_mixins import ViewMixinDynamicConfigurationFormClass


class DocumentTypeFileMetadataDriverConfigurationEditView(
    ExternalObjectViewMixin, ViewMixinDynamicConfigurationFormClass,
    SingleObjectEditView
):
    external_object_class = DocumentType
    external_object_permission = permission_document_type_file_metadata_setup
    external_object_pk_url_kwarg = 'document_type_id'
    slug_field = 'stored_driver_id'
    slug_url_kwarg = 'stored_driver_id'
    view_icon = icon_document_type_file_metadata_driver_configuration_edit

    def get_extra_context(self):
        return {
            'document_type': self.external_object,
            'navigation_object_list': ('document_type', 'object'),
            'object': self.object,
            'title': _(
                message='Edit file metadata driver '
                '"%(file_metadata_driver)s" settings for document type: '
                '%(document_type)s'
            ) % {
                'document_type': self.external_object,
                'file_metadata_driver': self.object
            }
        }

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'document_type_id': self.external_object.pk},
            viewname='file_metadata:document_type_file_metadata_driver_configuration_list'
        )

    def get_source_queryset(self):
        return DocumentTypeDriverConfiguration.valid.filter(
            document_type=self.external_object
        )


class DocumentTypeFileMetadataDriverConfigurationListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_class = DocumentType
    external_object_permission = permission_document_type_file_metadata_setup
    external_object_pk_url_kwarg = 'document_type_id'
    view_icon = icon_document_type_file_metadata_driver_configuration_list

    def get_extra_context(self):
        return {
            'document_type': self.external_object,
            'hide_object': True,
            'navigation_object_list': ('document_type',),
            'no_results_icon': icon_file_metadata_driver,
            'no_results_text': _(
                message='File metadata drivers extract embedded information '
                'from document files.'
            ),
            'no_results_title': _(
                message='No file metadata drivers available for this '
                'document type'
            ),
            'title': _(
                message='File metadata driver configuration for document '
                'type "%s".'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return DocumentTypeDriverConfiguration.valid.filter(
            document_type=self.external_object
        )


class DocumentTypeFileMetadataSubmitView(FormView):
    extra_context = {
        'submit_label': _(message='Submit'),
        'title': _(
            message='Submit all documents of a type for file metadata '
            'processing.'
        )
    }
    form_class = DocumentTypeFilteredSelectForm
    post_action_redirect = reverse_lazy(viewname='common:tools_list')
    view_icon = icon_document_type_file_metadata_submit

    def get_form_extra_kwargs(self):
        return {
            'allow_multiple': True,
            'permission': permission_file_metadata_submit,
            'user': self.request.user
        }

    def form_valid(self, form):
        queryset_documents = Document.valid.all()

        count = 0
        for document_type in form.cleaned_data['document_type']:
            for document in document_type.documents.filter(pk__in=queryset_documents.values('pk')):
                document.submit_for_file_metadata_processing(
                    user=self.request.user
                )
                count += 1

        messages.success(
            message=_(
                message='%(count)d documents added to the file metadata '
                'processing queue.'
            ) % {
                'count': count
            }, request=self.request
        )

        return HttpResponseRedirect(
            redirect_to=self.get_success_url()
        )
