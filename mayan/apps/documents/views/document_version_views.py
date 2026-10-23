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
    ConfirmView, FormView, MultipleObjectConfirmActionView,
    MultipleObjectDeleteView, SingleObjectCreateView, SingleObjectDetailView,
    SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..classes import DocumentVersionModification
from ..events import event_document_viewed
from ..forms.document_version_forms import (
    DocumentVersionForm, DocumentVersionModificationBackendForm,
    DocumentVersionPreviewForm
)
from ..forms.misc_forms import PageNumberForm
from ..icons import (
    icon_document_version_active, icon_document_version_create,
    icon_document_version_delete_multiple, icon_document_version_edit,
    icon_document_version_list, icon_document_version_modification,
    icon_document_version_preview, icon_document_version_print,
    icon_document_version_transformation_clear_multiple,
    icon_document_version_transformations_clone
)
from ..links.document_version_links import link_document_version_create
from ..models.document_models import Document
from ..models.document_version_models import DocumentVersion
from ..permissions import (
    permission_document_version_create, permission_document_version_delete,
    permission_document_version_edit, permission_document_version_print,
    permission_document_version_view
)
from ..settings import setting_preview_height, setting_preview_width
from ..tasks import task_document_version_delete

from .misc_views import (
    DocumentPrintBaseView, DocumentPrintPDFBaseView, PrintFormView
)
from .view_mixins import RecentDocumentViewMixin

logger = logging.getLogger(name=__name__)


class DocumentVersionActiveView(ExternalObjectViewMixin, ConfirmView):
    external_object_permission = permission_document_version_edit
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    view_icon = icon_document_version_active

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'submit_label': _(message='Set active'),
            'title': _(
                message='Make the document version "%s" the active version?'
            ) % self.external_object
        }

    def view_action(self, form=None):
        self.external_object._event_actor = self.request.user
        self.external_object.active_set()
        messages.success(
            message=_(
                message='Successfully changed the active document version.'
            ), request=self.request
        )


class DocumentVersionCreateView(
    ExternalObjectViewMixin, SingleObjectCreateView
):
    external_object_permission = permission_document_version_create
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    form_class = DocumentVersionForm
    view_icon = icon_document_version_create

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='Create a document version for document: %s'
            ) % self.external_object
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'document': self.external_object
        }

    def get_queryset(self):
        return self.external_object.versions.all()


class DocumentVersionDeleteView(MultipleObjectDeleteView):
    object_permission = permission_document_version_delete
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    success_message_single = _(
        message='Document version "%(object)s" deletion queued successfully.'
    )
    success_message_singular = _(
        message='%(count)d document version deletion queued successfully.'
    )
    success_message_plural = _(
        message='%(count)d document version deletions queued successfully.'
    )
    title_single = _(message='Delete document version "%(object)s".')
    title_singular = _(message='Delete %(count)d document version.')
    title_plural = _(message='Delete %(count)d document versions.')
    view_icon = icon_document_version_delete_multiple

    def get_extra_context(self, **kwargs):
        context = {
            'message': _(
                message='The process will be performed in the background.'
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
                'document_id': self.object_list[0].document_id
            }, viewname='documents:document_version_list'
        )

    def object_action(self, instance, form=None):
        task_document_version_delete.apply_async(
            kwargs={
                'document_version_id': instance.pk,
                'user_id': self.request.user.pk
            }
        )


class DocumentVersionEditView(SingleObjectEditView):
    form_class = DocumentVersionForm
    object_permission = permission_document_version_edit
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    view_icon = icon_document_version_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit document version: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'document_version_id': self.object.pk},
            viewname='documents:document_version_preview'
        )


class DocumentVersionListView(
    ExternalObjectViewMixin, RecentDocumentViewMixin, SingleObjectListView
):
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    object_permission = permission_document_version_view
    recent_document_view_document_property_name = 'external_object'
    view_icon = icon_document_version_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'list_as_items': True,
            'no_results_icon': icon_document_version_list,
            'no_results_main_link': link_document_version_create.resolve(
                context=RequestContext(
                    dict_={'object': self.external_object},
                    request=self.request
                )
            ),
            'no_results_text': _(
                message='Versions are views that can display document file '
                'pages as they are, remap or merge them into different '
                'layouts.'
            ),
            'no_results_title': _(message='No versions available'),
            'object': self.external_object,
            'table_cell_container_classes': 'td-container-thumbnail',
            'title': _(
                message='Versions of document: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.versions.order_by('-timestamp')


class DocumentVersionModifyView(ExternalObjectViewMixin, FormView):
    external_object_permission = permission_document_version_edit
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    form_class = DocumentVersionModificationBackendForm
    view_icon = icon_document_version_modification

    def dispatch(self, request, *args, **kwargs):
        results = super().dispatch(request=request, *args, **kwargs)
        self.external_object.document.add_as_recent_document_for_user(
            user=request.user
        )

        return results

    def form_valid(self, form):
        DocumentVersionModification.get(
            name=form.cleaned_data['backend']
        ).execute(
            document_version=self.external_object,
            user=self.request.user
        )

        messages.success(
            message=_(
                message='Document version modification backend queued '
                'successfully.'
            ), request=self.request
        )

        return super().form_valid(form=form)

    def get_extra_context(self):
        context = {
            'object': self.external_object,
            'submit_label': _(message='Save'),
            'title': _(
                message='Execute version modification action for document '
                'version: %s'
            ) % self.external_object
        }

        return context


class DocumentVersionPreviewView(SingleObjectDetailView):
    form_class = DocumentVersionPreviewForm
    object_permission = permission_document_version_view
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    template_name = 'appearance/viewport_fill.html'
    view_icon = icon_document_version_preview

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
            'title': _(
                message='Preview of document version: %s'
            ) % self.object
        }

    def get_form_extra_kwargs(self):
        transformation_instance_list = (
            TransformationResize(
                height=setting_preview_height.value,
                width=setting_preview_width.value
            ),
        )

        return {'transformation_instance_list': transformation_instance_list}


class DocumentVersionPrintFormView(PrintFormView):
    external_object_permission = permission_document_version_print
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    print_view_name = 'documents:document_version_print_view'
    print_view_kwarg = 'document_version_id'
    view_icon = icon_document_version_print

    def _add_recent_document(self):
        self.external_object.document.add_as_recent_document_for_user(
            user=self.request.user
        )


class DocumentVersionPrintView(DocumentPrintBaseView):
    external_object_permission = permission_document_version_print
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    print_pdf_view_name = 'documents:document_version_print_pdf_view'
    print_pdf_view_kwarg = 'document_version_id'
    view_icon = icon_document_version_print

    def _add_recent_document(self):
        self.external_object.document.add_as_recent_document_for_user(
            user=self.request.user
        )


class DocumentVersionPrintPDFView(DocumentPrintPDFBaseView):
    external_object_permission = permission_document_version_print
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    view_icon = icon_document_version_print


class DocumentVersionTransformationsClearView(
    MultipleObjectConfirmActionView
):
    object_permission = permission_transformation_delete
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    success_message = _(
        message='Transformation clear request processed for %(count)d '
        'document version.'
    )
    success_message_plural = _(
        message='Transformation clear request processed for %(count)d '
        'document versions.'
    )
    view_icon = icon_document_version_transformation_clear_multiple

    def get_extra_context(self):
        result = {
            'title': ngettext(
                singular='Clear all the page transformations for the selected document version?',
                plural='Clear all the page transformations for the selected document version?',
                number=self.object_list.count()
            )
        }

        if self.object_list.count() == 1:
            result.update(
                {
                    'object': self.object_list.first(),
                    'title': _(
                        message='Clear all the page transformations for the '
                        'document version: %s?'
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
                    'document version: %(document_version)s; %(error)s.'
                ) % {
                    'document_version': instance, 'error': exception
                }, request=self.request
            )


class DocumentVersionTransformationsCloneView(
    ExternalObjectViewMixin, FormView
):
    external_object_permission = permission_transformation_edit
    external_object_pk_url_kwarg = 'document_version_id'
    external_object_queryset = DocumentVersion.valid.all()
    form_class = PageNumberForm
    view_icon = icon_document_version_transformations_clone

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
                        'document version: %(document_version)s; %(error)s.'
                    ) % {
                        'document_version': self.external_object,
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
                message='Clone page transformations of document version: %s'
            ) % self.external_object
        }

        return context
