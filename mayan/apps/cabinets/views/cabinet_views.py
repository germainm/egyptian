from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.documents.views.document_views import DocumentListView
from mayan.apps.views.generics import (
    SingleObjectCreateView, SingleObjectDeleteView, SingleObjectEditView,
    SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_cabinet, icon_cabinet_child_add, icon_cabinet_create,
    icon_cabinet_delete, icon_cabinet_detail, icon_cabinet_edit,
    icon_cabinet_list
)
from ..links import link_cabinet_child_add, link_cabinet_create
from ..models import Cabinet
from ..permissions import (
    permission_cabinet_create, permission_cabinet_delete,
    permission_cabinet_edit, permission_cabinet_view
)
from ..widgets import jstree_data


class CabinetCreateView(SingleObjectCreateView):
    fields = ('label',)
    model = Cabinet
    post_action_redirect = reverse_lazy(viewname='cabinets:cabinet_list')
    view_icon = icon_cabinet_create
    view_permission = permission_cabinet_create

    def get_extra_context(self):
        return {
            'title': _(message='Create cabinet')
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class CabinetChildAddView(ExternalObjectViewMixin, SingleObjectCreateView):
    fields = ('label',)
    external_object_class = Cabinet
    external_object_permission = permission_cabinet_create
    external_object_pk_url_kwarg = 'cabinet_id'
    view_icon = icon_cabinet_child_add

    def get_extra_context(self):
        return {
            'title': _(
                message='Add new level to: %s'
            ) % self.external_object.get_full_path(),
            'object': self.external_object
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'parent': self.external_object
        }

    def get_queryset(self):
        return self.external_object.get_descendants()


class CabinetDeleteView(SingleObjectDeleteView):
    model = Cabinet
    object_permission = permission_cabinet_delete
    post_action_redirect = reverse_lazy(viewname='cabinets:cabinet_list')
    pk_url_kwarg = 'cabinet_id'
    view_icon = icon_cabinet_delete

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Delete the cabinet: %s?') % self.object
        }


class CabinetDetailView(ExternalObjectViewMixin, DocumentListView):
    external_object_class = Cabinet
    external_object_permission = permission_cabinet_view
    external_object_pk_url_kwarg = 'cabinet_id'
    template_name = 'cabinets/cabinet_details.html'
    view_icon = icon_cabinet_detail

    def get_document_queryset(self):
        return self.external_object.get_documents(
            permission=permission_document_view, user=self.request.user
        )

    def get_extra_context(self, **kwargs):
        context = super().get_extra_context(**kwargs)

        context.update(
            {
                'column_class': 'col-xs-12 col-sm-6 col-md-4 col-lg-3',
                'hide_links': True,
                'jstree_data': [
                    jstree_data(
                        node=self.external_object.get_root(),
                        selected_node=self.external_object
                    )
                ],
                'list_as_items': True,
                'no_results_icon': icon_cabinet,
                'no_results_main_link': link_cabinet_child_add.resolve(
                    context=RequestContext(
                        dict_={
                            'object': self.external_object
                        }, request=self.request
                    )
                ),
                'no_results_text': _(
                    message='Cabinet levels can contain documents or other '
                    'cabinet sub levels. To add documents to a cabinet, '
                    'select the cabinet view of a document view.'
                ),
                'no_results_title': _(message='This cabinet level is empty'),
                'object': self.external_object,
                'title': _(
                    message='Details of cabinet: %s'
                ) % self.external_object.get_full_path()
            }
        )

        return context


class CabinetEditView(SingleObjectEditView):
    fields = ('label',)
    model = Cabinet
    object_permission = permission_cabinet_edit
    post_action_redirect = reverse_lazy(viewname='cabinets:cabinet_list')
    pk_url_kwarg = 'cabinet_id'
    view_icon = icon_cabinet_edit

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Edit cabinet: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class CabinetListView(SingleObjectListView):
    object_permission = permission_cabinet_view
    view_icon = icon_cabinet_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'title': _(message='Cabinets'),
            'no_results_icon': icon_cabinet,
            'no_results_main_link': link_cabinet_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Cabinets are a multi-level method to organize '
                'documents. Each cabinet can contain documents as '
                'well as other sub level cabinets.'
            ),
            'no_results_title': _(message='No cabinets available')
        }

    def get_source_queryset(self):
        return Cabinet.objects.root_nodes()
