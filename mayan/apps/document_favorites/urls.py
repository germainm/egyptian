from django.urls import re_path

from .api_views import (
    APIFavoriteDocumentDetailView, APIFavoriteDocumentListView
)
from .views import (
    FavoriteAddView, FavoriteDocumentListView, FavoriteRemoveView
)

urlpatterns = [
    re_path(
        route=r'^documents/favorites/$', name='document_favorite_list',
        view=FavoriteDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/add_to_favorites/$',
        name='document_favorite_add', view=FavoriteAddView.as_view()
    ),
    re_path(
        route=r'^documents/multiple/add_to_favorites/$',
        name='document_favorite_add_multiple', view=FavoriteAddView.as_view()
    ),
    re_path(
        route=r'^documents/(?P<document_id>\d+)/remove_from_favorites/$',
        name='document_favorite_remove', view=FavoriteRemoveView.as_view()
    ),
    re_path(
        route=r'^documents/multiple/remove_from_favorites/$',
        name='document_favorite_remove_multiple',
        view=FavoriteRemoveView.as_view()
    )
]

api_urls = [
    re_path(
        route=r'^documents/favorites/$',
        name='favoritedocument-list',
        view=APIFavoriteDocumentListView.as_view()
    ),
    re_path(
        route=r'^documents/favorites/(?P<favorite_document_id>[0-9]+)/$',
        name='favoritedocument-detail',
        view=APIFavoriteDocumentDetailView.as_view()
    )
]
