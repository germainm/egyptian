import logging

from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.converter.layers import layer_saved_transformations
from mayan.apps.converter.permissions import (
    permission_transformation_delete, permission_transformation_edit
)
from mayan.apps.converter.transformations import TransformationResize
from mayan.apps.views.generics import (
    FormView, MultipleObjectConfirmActionView, MultipleObjectDeleteView,
    SingleObjectDetailView, SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..events import event_document_viewed
from ..forms.document_file_forms import (
    DocumentFileForm, DocumentFilePreviewForm, DocumentFilePropertiesForm
)
from ..forms.misc_forms import PageNumberForm
from ..icons import (
    icon_document_file_delete, icon_document_file_edit,
    icon_document_file_introspect, icon_document_file_list,
    icon_document_file_preview, icon_document_file_print,
    icon_document_file_properties_detail,
    icon_document_file_transformation_list_clear,
    icon_document_file_transformation_list_clone
)
from ..literals import DEFAULT_DOCUMENT_FILE_ACTION_NAME
from ..models.document_file_models import DocumentFile
from ..models.document_models import Document
from ..permissions import (
    permission_document_file_delete, permission_document_file_edit,
    permission_document_file_print, permission_document_file_tools,
    permission_document_file_view
)
from ..settings import setting_preview_height, setting_preview_width
from ..tasks import task_document_file_delete, task_document_file_size_update

from .misc_views import (
    DocumentPrintBaseView, DocumentPrintPDFBaseView, PrintFormView
)

logger = logging.getLogger(name=__name__)


class DocumentFileDeleteView(MultipleObjectDeleteView):
    error_message = _(
        message='Error deleting document file "%(instance)s"; %(exception)s'
    )
    object_permission = permission_document_file_delete
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    success_message_single = _(
        message='Document file "%(object)s" deletion queued successfully.'
    )
    success_message_singular = _(
        message='%(count)d document file deletion queued successfully.'
    )
    success_message_plural = _(
        message='%(count)d document files deletions queued successfully.'
    )
    title_single = _(message='Delete document file: %(object)s.')
    title_singular = _(message='Delete the %(count)d selected document file.')
    title_plural = _(message='Delete the %(count)d selected document files.')
    view_icon = icon_document_file_delete

    def get_extra_context(self):
        context = {
            'message': _(
                message='All document files pages from this document file '
                'and the document version pages linked to them will be '
                'deleted too. The process will be performed in the '
                'background.'
            )
        }

        if self.object_list.count() > 1:
            context.update(
                {
                    'object': self.object_list.first().document
                }
            )

        return context

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'document_id': self.object_list.first().document.pk
            }, viewname='documents:document_file_list'
        )

    def object_action(self, instance, form=None):
        task_document_file_delete.apply_async(
            kwargs={
                'document_file_id': instance.pk,
                'user_id': self.request.user.pk
            }
        )


class DocumentFileEditView(SingleObjectEditView):
    form_class = DocumentFileForm
    object_permission = permission_document_file_edit
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit document file: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'document_file_id': self.object.pk},
            viewname='documents:document_file_preview'
        )


class DocumentFileIntrospectView(MultipleObjectConfirmActionView):
    object_permission = permission_document_file_tools
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    success_message = _(
        message='%(count)d document file queued for introspection.'
    )
    success_message_plural = _(
        message='%(count)d document files queued for introspection.'
    )
    view_icon = icon_document_file_introspect

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'submit_label': _(message='Introspect'),
            'title': ngettext(
                singular='Introspect the selected document file?',
                plural='Introspect the selected document files?',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Introspect the document file: %s?'
                    ) % queryset.first()
                }
            )

        result['message'] = _(
            message='The document file will be re-examined for file size, '
            'page count, checksum, and its related document version pages '
            're-created. All transformations will be lost.'
        )

        return result

    def object_action(self, form, instance):
        task_document_file_size_update.apply_async(
            kwargs={
                'action_name': DEFAULT_DOCUMENT_FILE_ACTION_NAME,
                'document_file_id': instance.pk,
                'is_document_upload_sequence': True,
                'user_id': self.request.user.pk
            }
        )


class DocumentFileListView(ExternalObjectViewMixin, SingleObjectListView):
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    no_results_main_link = None
    object_permission = permission_document_file_view
    view_icon = icon_document_file_list

    @classmethod
    def get_no_results_context(cls, document=None, request=None):
        context = {
            'no_results_icon': icon_document_file_list,
            'no_results_text': _(
                message='File are the actual files that were uploaded for '
                'each document. Their contents needs to be mapped to a '
                'version before it can be used.'
            ),
            'no_results_title': _(message='No files available')
        }

        main_link = cls.no_results_main_link

        if document and main_link:
            resolved_main_link = main_link.resolve(
                context=RequestContext(
                    dict_={'object': document}, request=request
                )
            )
            context['no_results_main_link'] = resolved_main_link

        return context

    def get_document(self):
        document = self.external_object
        document.add_as_recent_document_for_user(user=self.request.user)
        return document

    def get_extra_context(self):
        document = self.get_document()
        context = {
            'hide_object': True,
            'list_as_items': True,
            'object': document,
            'table_cell_container_classes': 'td-container-thumbnail',
            'title': _(message='Files of document: %s') % document
        }
        context.update(
            DocumentFileListView.get_no_results_context(
                document=document, request=self.request
            )
        )
        return context

    def get_source_queryset(self):
        return self.get_document().files.order_by('-timestamp')


class DocumentFilePreviewView(SingleObjectDetailView):
    form_class = DocumentFilePreviewForm
    object_permission = permission_document_file_view
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    template_name = 'appearance/viewport_fill.html'
    view_icon = icon_document_file_preview

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        self.object.document.add_as_recent_document_for_user(
            user=request.user
        )
        event_document_viewed.commit(
            actor=request.user, action_object=self.object,
            target=self.object.document
        )

        return result

    def get_extra_context(self):
        return {
            'hide_labels': True,
            'object': self.object,
            'title': _(message='Preview of document file: %s') % self.object
        }

    def get_form_extra_kwargs(self):
        transformation_instance_list = (
            TransformationResize(
                height=setting_preview_height.value,
                width=setting_preview_width.value
            ),
        )

        return {'transformation_instance_list': transformation_instance_list}


class DocumentFilePrintFormView(PrintFormView):
    external_object_permission = permission_document_file_print
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    print_view_name = 'documents:document_file_print_view'
    print_view_kwarg = 'document_file_id'
    view_icon = icon_document_file_print

    def _add_recent_document(self):
        self.external_object.document.add_as_recent_document_for_user(
            user=self.request.user
        )


class DocumentFilePrintView(DocumentPrintBaseView):
    external_object_permission = permission_document_file_print
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    print_pdf_view_name = 'documents:document_file_print_pdf_view'
    print_pdf_view_kwarg = 'document_file_id'
    view_icon = icon_document_file_print

    def _add_recent_document(self):
        self.external_object.document.add_as_recent_document_for_user(
            user=self.request.user
        )


class DocumentFilePrintPDFView(DocumentPrintPDFBaseView):
    external_object_permission = permission_document_file_print
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_print


class DocumentFilePropertiesView(SingleObjectDetailView):
    form_class = DocumentFilePropertiesForm
    object_permission = permission_document_file_view
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_properties_detail

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        self.object.document.add_as_recent_document_for_user(
            user=request.user
        )
        return result

    def get_extra_context(self):
        return {
            'document_file': self.object,
            'object': self.object,
            'title': _(message='Properties of document file: %s') % self.object
        }


class DocumentFileTransformationsClearView(MultipleObjectConfirmActionView):
    object_permission = permission_transformation_delete
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    success_message = _(
        message='Transformation clear request processed for %(count)d '
        'document file.'
    )
    success_message_plural = _(
        message='Transformation clear request processed for %(count)d '
        'document files.'
    )
    view_icon = icon_document_file_transformation_list_clear

    def get_extra_context(self):
        result = {
            'title': ngettext(
                singular='Clear all the page transformations for the selected document file?',
                plural='Clear all the page transformations for the selected document files?',
                number=self.object_list.count()
            )
        }

        if self.object_list.count() == 1:
            result.update(
                {
                    'object': self.object_list.first(),
                    'title': _(
                        message='Clear all the page transformations for the '
                        'document file: %s?'
                    ) % self.object_list.first()
                }
            )

        return result

    def object_action(self, form, instance):
        try:
            for page in instance.pages.all():
                layer_saved_transformations.get_transformations_for(
                    obj=page
                ).delete()
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error deleting the page transformations for '
                    'document file: %(document_file)s; %(error)s.'
                ) % {
                    'document_file': instance, 'error': exception
                }, request=self.request
            )


class DocumentFileTransformationsCloneView(ExternalObjectViewMixin, FormView):
    external_object_permission = permission_transformation_edit
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    form_class = PageNumberForm
    view_icon = icon_document_file_transformation_list_clone

    def dispatch(self, request, *args, **kwargs):
        results = super().dispatch(request=request, *args, **kwargs)
        self.external_object.document.add_as_recent_document_for_user(
            user=request.user
        )

        return results

    def form_valid(self, form):
        try:
            layer_saved_transformations.copy_transformations(
                delete_existing=True, source=form.cleaned_data['page'],
                targets=form.cleaned_data['page'].siblings.exclude(
                    pk=form.cleaned_data['page'].pk
                )
            )
        except Exception as exception:
            if settings.DEBUG:
                raise
            else:
                messages.error(
                    message=_(
                        message='Error cloning the page transformations for '
                        'document file: %(document_file)s; %(error)s.'
                    ) % {
                        'document_file': self.external_object,
                        'error': exception
                    }, request=self.request
                )
        else:
            messages.success(
                message=_(message='Transformations cloned successfully.'),
                request=self.request
            )

        return super().form_valid(form=form)

    def get_form_extra_kwargs(self):
        return {'instance': self.external_object}

    def get_extra_context(self):
        context = {
            'object': self.external_object,
            'submit_label': _(message='Clone'),
            'title': _(
                message='Clone page transformations of document file: %s'
            ) % self.external_object
        }

        return context
