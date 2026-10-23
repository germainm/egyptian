from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import menu_multi_item, menu_object
from mayan.apps.documents.menus import menu_documents
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.user_management.dashboards import dashboard_user

from .dashboard_widgets import DashboardWidgetUserFavoriteDocuments
from .links import (
    link_document_favorites_add_multiple, link_document_favorites_add_single,
    link_document_favorites_list, link_document_favorites_remove_multiple,
    link_document_favorites_remove_single
)


class DocumentFavoritesApp(MayanAppConfig):
    app_namespace = 'document_favorites'
    app_url = 'document_favorites'
    has_app_translations = True
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.document_favorites'
    verbose_name = _(message='Document favorites')

    def ready(self):
        super().ready()

        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        FavoriteDocument = self.get_model(model_name='FavoriteDocument')
        FavoriteDocumentProxy = self.get_model(
            model_name='FavoriteDocumentProxy'
        )

        ModelPermission.register_inheritance(
            model=FavoriteDocument, related='document'
        )

        SourceColumn(
            func=lambda context: context['object'].favorites.get(
                user=context['request'].user
            ).datetime_added, include_label=True, is_sortable=True,
            label=_(message='Date and time added'), name='datetime_added',
            sort_field='favorites__datetime_added',
            source=FavoriteDocumentProxy
        )

        dashboard_user.add_widget(
            order=3, widget=DashboardWidgetUserFavoriteDocuments
        )

        menu_documents.bind_links(
            links=(link_document_favorites_list,), position=2
        )
        menu_multi_item.bind_links(
            links=(
                link_document_favorites_add_multiple,
                link_document_favorites_remove_multiple
            ), position=0, sources=(Document,)
        )
        menu_object.bind_links(
            links=(
                link_document_favorites_add_single,
                link_document_favorites_remove_single
            ), position=0, sources=(Document,)
        )
