import logging

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.databases.classes import ModelQueryFields
from mayan.apps.views.generics import (
    MultipleObjectFormActionView, SingleObjectDetailView,
    SingleObjectEditView, SingleObjectListView
)

from ..events import event_document_viewed
from ..forms.document_forms import DocumentForm, DocumentPropertiesForm
from ..forms.document_type_forms import DocumentTypeFilteredSelectForm
from ..icons import (
    icon_document_list, icon_document_preview,
    icon_document_properties_detail, icon_document_properties_edit,
    icon_document_type_change_multiple
)
from ..models.document_models import Document
from ..models.document_type_models import DocumentType
from ..permissions import (
    permission_document_change_type, permission_document_properties_edit,
    permission_document_view
)

from .document_version_views import DocumentVersionPreviewView

logger = logging.getLogger(name=__name__)


class DocumentListView(SingleObjectListView):
    object_permission = permission_document_view
    view_icon = icon_document_list

    def get_context_data(self, **kwargs):
        try:
            return super().get_context_data(**kwargs)
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error retrieving document list: %(exception)s.'
                ) % {
                    'exception': exception
                }, request=self.request
            )

            if settings.DEBUG or settings.TESTING:
                raise

            self.object_list = Document.valid.none()
            return super().get_context_data(**kwargs)

    def get_document_queryset(self):
        return Document.valid.all()

    def get_extra_context(self):
        return {
            'hide_links': True,
            'hide_object': True,
            'list_as_items': True,
            'no_results_icon': icon_document_list,
            'no_results_text': _(
                message='This could mean that no documents have been '
                'uploaded or that your user account has not been granted '
                'the view permission for any document or document type.'
            ),
            'no_results_title': _(message='No documents available'),
            'title': _(message='All documents')
        }

    def get_source_queryset(self):
        model_query_fields = ModelQueryFields.get(model=Document)
        return model_query_fields.get_queryset_apply(
            queryset=self.get_document_queryset()
        )


class DocumentTypeChangeView(MultipleObjectFormActionView):
    form_class = DocumentTypeFilteredSelectForm
    object_permission = permission_document_change_type
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='Document type change request performed on %(count)d '
        'document.'
    )
    success_message_plural = _(
        message='Document type change request performed on %(count)d '
        'documents.'
    )
    view_icon = icon_document_type_change_multiple

    def get_extra_context(self):
        result = {
            'submit_label': _(message='Change type'),
            'title': ngettext(
                singular='Change the type of the selected document.',
                plural='Change the type of the selected documents.',
                number=self.object_list.count()
            )
        }

        if self.object_list.count() == 1:
            result.update(
                {
                    'object': self.object_list.first(),
                    'title': _(
                        message='Change the type of the document: %s'
                    ) % self.object_list.first()
                }
            )

        return result

    def get_form_extra_kwargs(self):
        result = {
            'permission': permission_document_change_type,
            'user': self.request.user
        }

        if self.object_list.count() == 1:
            result['queryset'] = DocumentType.objects.exclude(
                pk=self.object_list.first().document_type.pk
            )

        return result

    def object_action(self, form, instance):
        instance.document_type_change(
            document_type=form.cleaned_data['document_type'],
            user=self.request.user
        )

        messages.success(
            message=_(
                message='Document type for "%s" changed successfully.'
            ) % instance, request=self.request
        )


class DocumentPreviewView(DocumentVersionPreviewView):
    object_permission = permission_document_view
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    view_icon = icon_document_preview

    def dispatch(self, request, *args, **kwargs):
        result = super(
            DocumentVersionPreviewView, self
        ).dispatch(request=request, *args, **kwargs)
        self.object.add_as_recent_document_for_user(user=request.user)
        event_document_viewed.commit(
            actor=request.user, target=self.object
        )

        return result

    def get_extra_context(self):
        return {
            'hide_labels': True,
            'object': self.object,
            'title': _(message='Preview of document: %s') % self.object
        }


class DocumentPropertiesEditView(SingleObjectEditView):
    form_class = DocumentForm
    object_permission = permission_document_properties_edit
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    view_icon = icon_document_properties_edit

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        self.object.add_as_recent_document_for_user(user=request.user)
        return result

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(
                message='Edit properties of document: %s'
            ) % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'document_id': self.object.pk},
            viewname='documents:document_properties'
        )


class DocumentPropertiesView(SingleObjectDetailView):
    form_class = DocumentPropertiesForm
    object_permission = permission_document_view
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    view_icon = icon_document_properties_detail

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        self.object.add_as_recent_document_for_user(request.user)
        return result

    def get_extra_context(self):
        return {
            'document': self.object,
            'object': self.object,
            'title': _(message='Properties of document: %s') % self.object
        }
