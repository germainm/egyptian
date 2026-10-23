import logging

from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.views.generics import (
    AddRemoveView, SingleObjectCreateView, SingleObjectDeleteView,
    SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from .forms import WebLinkForm
from .icons import icon_web_link_setup
from .links import link_web_link_create
from .literals import TEXT_WEB_LINK_NO_RESULTS
from .models import ResolvedWebLink, WebLink
from .permissions import (
    permission_web_link_create, permission_web_link_delete,
    permission_web_link_edit, permission_web_link_instance_view,
    permission_web_link_view
)

logger = logging.getLogger(name=__name__)


class DocumentTypeWebLinksView(AddRemoveView):
    list_added_title = _(message='Web links enabled')
    list_available_title = _(message='Available web links')
    main_object_method_add_name = 'web_links_add'
    main_object_method_remove_name = 'web_links_remove'
    main_object_model = DocumentType
    main_object_permission = permission_document_type_edit
    main_object_pk_url_kwarg = 'document_type_id'
    related_field = 'web_links'
    secondary_object_model = WebLink
    secondary_object_permission = permission_web_link_edit

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(
                message='Web links to enable for document type: %s'
            ) % self.main_object
        }


class ResolvedWebLinkView(ExternalObjectViewMixin, RedirectView):
    external_object_pk_url_kwarg = 'document_id'
    external_object_permission = permission_web_link_instance_view
    external_object_queryset = Document.valid.all()

    def get_redirect_url(self, *args, **kwargs):
        return self.get_web_link().get_redirect(
            document=self.external_object, user=self.request.user
        ).url

    def get_web_link(self):
        return get_object_or_404(
            klass=self.get_web_link_queryset(), pk=self.kwargs['web_link_id']
        )

    def get_web_link_queryset(self):
        queryset = ResolvedWebLink.objects.get_for(
            document=self.external_object, user=self.request.user
        )
        return AccessControlList.objects.restrict_queryset(
            permission=permission_web_link_instance_view, queryset=queryset,
            user=self.request.user
        )


class WebLinkCreateView(SingleObjectCreateView):
    extra_context = {
        'title': _(message='Create new web link')
    }
    form_class = WebLinkForm
    post_action_redirect = reverse_lazy(
        viewname='web_links:web_link_list'
    )
    view_permission = permission_web_link_create

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class WebLinkDeleteView(SingleObjectDeleteView):
    model = WebLink
    object_permission = permission_web_link_delete
    pk_url_kwarg = 'web_link_id'
    post_action_redirect = reverse_lazy(
        viewname='web_links:web_link_list'
    )

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Delete web link: %s') % self.object
        }


class WebLinkDocumentTypesView(AddRemoveView):
    list_added_title = _(message='Document types enabled')
    list_available_title = _(message='Available document types')
    main_object_method_add_name = 'document_types_add'
    main_object_method_remove_name = 'document_types_remove'
    main_object_model = WebLink
    main_object_permission = permission_web_link_edit
    main_object_pk_url_kwarg = 'web_link_id'
    related_field = 'document_types'
    secondary_object_model = DocumentType
    secondary_object_permission = permission_document_type_edit

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(
                message='Document type for which to enable web link: %s'
            ) % self.main_object
        }


class WebLinkEditView(SingleObjectEditView):
    form_class = WebLinkForm
    model = WebLink
    object_permission = permission_web_link_edit
    pk_url_kwarg = 'web_link_id'
    post_action_redirect = reverse_lazy(
        viewname='web_links:web_link_list'
    )

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Edit web link: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class WebLinkListView(SingleObjectListView):
    object_permission = permission_web_link_view

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_web_link_setup,
            'no_results_main_link': link_web_link_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': TEXT_WEB_LINK_NO_RESULTS,
            'no_results_title': _(
                message='There are no web links'
            ),
            'title': _(message='Web links')
        }

    def get_source_queryset(self):
        return self.get_web_link_queryset()

    def get_web_link_queryset(self):
        return WebLink.objects.all()


class DocumentWebLinkListView(ExternalObjectViewMixin, WebLinkListView):
    external_object_permission = permission_web_link_instance_view
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    object_permission = permission_web_link_instance_view

    def get_extra_context(self):
        return {
            'document': self.external_object,
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_web_link_setup,
            'no_results_text': TEXT_WEB_LINK_NO_RESULTS,
            'no_results_title': _(
                message='There are no web links for this document'
            ),
            'object': self.external_object,
            'title': _(message='Web links for document: %s') % self.external_object
        }

    def get_web_link_queryset(self):
        return ResolvedWebLink.objects.get_for(
            document=self.external_object, user=self.request.user
        )
