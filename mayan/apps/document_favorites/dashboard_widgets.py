from django.apps import apps
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.dashboards.classes import DashboardWidgetList

from .links import link_document_favorites_list


class DashboardWidgetUserFavoriteDocuments(DashboardWidgetList):
    columns = ('datetime_added', 'label',)
    empty_link_text = _(message='Browse documents')
    empty_link_url = reverse_lazy(viewname='documents:document_list')
    empty_text = _(
        message='You have not marked any documents as favorites yet.'
    )
    icon = link_document_favorites_list.get_icon()
    label = link_document_favorites_list.text
    link = reverse_lazy(
        viewname=link_document_favorites_list.view
    )

    def get_object_list(self):
        FavoriteDocument = apps.get_model(
            app_label='document_favorites', model_name='FavoriteDocument'
        )

        return FavoriteDocument.valid.get_for_user(
            user=self.request.user
        )
