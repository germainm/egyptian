from django.template import RequestContext
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.views.generics import MultipleObjectFormActionView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms import CabinetListForm
from ..icons import (
    icon_cabinet, icon_document_cabinet_add, icon_document_cabinet_list,
    icon_document_cabinet_remove
)
from ..links import link_document_cabinet_add
from ..models import Cabinet
from ..permissions import (
    permission_cabinet_add_document, permission_cabinet_remove_document,
    permission_cabinet_view
)

from .cabinet_views import CabinetListView


class DocumentCabinetAddView(MultipleObjectFormActionView):
    form_class = CabinetListForm
    object_permission = permission_cabinet_add_document
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_single = _(
        message='Document "%(object)s" added to cabinets successfully.'
    )
    success_message_singular = _(
        message='%(count)d document added to cabinets successfully.'
    )
    success_message_plural = _(
        message='%(count)d documents added to cabinets successfully.'
    )
    title_plural = _(message='Add %(count)d documents to cabinets.')
    title_single = _(message='Add document "%(object)s" to cabinets.')
    title_singular = _(message='Add %(count)d document to cabinets.')
    view_icon = icon_document_cabinet_add

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Add')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_form_extra_kwargs(self):
        kwargs = {
            'help_text': _(
                message='Cabinets to which the selected documents will be '
                'added.'
            ),
            'permission': permission_cabinet_add_document,
            'queryset': Cabinet.objects.all(),
            'user': self.request.user
        }

        if self.object_list.count() == 1:
            kwargs.update(
                {
                    'queryset': Cabinet.objects.exclude(
                        pk__in=self.object_list.first().cabinets.all()
                    )
                }
            )

        return kwargs

    def object_action(self, form, instance):
        for cabinet in form.cleaned_data['cabinets']:
            AccessControlList.objects.check_access(
                obj=cabinet, permission=permission_cabinet_add_document,
                user=self.request.user
            )

            cabinet.document_add(document=instance, user=self.request.user)


class DocumentCabinetListView(ExternalObjectViewMixin, CabinetListView):
    external_object_permission = permission_cabinet_view
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    view_icon = icon_document_cabinet_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'no_results_icon': icon_cabinet,
            'no_results_main_link': link_document_cabinet_add.resolve(
                context=RequestContext(
                    dict_={
                        'object': self.external_object
                    }, request=self.request
                )
            ),
            'no_results_text': _(
                message='Documents can be added to many cabinets.'
            ),
            'no_results_title': _(
                message='This document is not in any cabinet'
            ),
            'object': self.external_object,
            'title': _(
                message='Cabinets containing document: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.get_cabinets(
            permission=permission_cabinet_view, user=self.request.user
        )


class DocumentCabinetRemoveView(MultipleObjectFormActionView):
    form_class = CabinetListForm
    object_permission = permission_cabinet_remove_document
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_single = _(
        message='Document "%(object)s" removed from cabinets successfully.'
    )
    success_message_singular = _(
        message='%(count)d document removed from cabinets successfully.'
    )
    success_message_plural = _(
        message='%(count)d documents removed from cabinets successfully.'
    )
    title_plural = _(message='Remove %(count)d documents from cabinets.')
    title_single = _(message='Remove document "%(object)s" from cabinets.')
    title_singular = _(message='Remove %(count)d document from cabinets.')
    view_icon = icon_document_cabinet_remove

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Remove')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_form_extra_kwargs(self):
        kwargs = {
            'help_text': _(
                message='Cabinets from which the selected documents will be '
                'removed.'
            ),
            'permission': permission_cabinet_remove_document,
            'queryset': Cabinet.objects.all(),
            'user': self.request.user
        }

        if self.object_list.count() == 1:
            kwargs.update(
                {
                    'queryset': self.object_list.first().cabinets.all()
                }
            )

        return kwargs

    def object_action(self, form, instance):
        for cabinet in form.cleaned_data['cabinets']:
            AccessControlList.objects.check_access(
                obj=cabinet, permission=permission_cabinet_remove_document,
                user=self.request.user
            )

            cabinet.document_remove(
                document=instance, user=self.request.user
            )
