from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import (
    icon_saved_resultset_delete_single, icon_saved_resultset_list,
    icon_saved_resultset_result_list, icon_search, icon_search_advanced,
    icon_search_again, icon_search_backend_reindex, icon_search_model_detail,
    icon_search_model_list
)
from .permissions import permission_search_tools
from .search_backends import SearchBackend


def condition_search_backend_supports_reindexing(context, resolved_object):
    search_backend_class = SearchBackend.get_class()
    return search_backend_class.feature_reindex


link_saved_resultset_list = Link(
    icon=icon_saved_resultset_list, text=_(message='Saved resultsets'),
    view='search:saved_resultset_list'
)
link_saved_resultset_delete_single = Link(
    args=('resolved_object.pk',), icon=icon_saved_resultset_delete_single,
    tags='dangerous', text=_(message='Delete'),
    view='search:saved_resultset_delete_single'
)
link_saved_resultset_result_list = Link(
    args=('resolved_object.pk',), icon=icon_saved_resultset_result_list,
    text=_(message='Results'), view='search:saved_resultset_result_list'
)

link_search = Link(
    args='search_model.full_name', icon=icon_search,
    text=_(message='Basic search'), view='search:search_simple'
)
link_search_advanced = Link(
    args='search_model.full_name', icon=icon_search_advanced,
    text=_(message='Advanced search'), view='search:search_advanced'
)
link_search_again = Link(
    args='search_model.full_name', icon=icon_search_again,
    keep_query=True, text=_(message='Search again'), view='search:search_again'
)
link_search_backend_reindex = Link(
    condition=condition_search_backend_supports_reindexing,
    icon=icon_search_backend_reindex, permission=permission_search_tools,
    text=_(message='Reindex search backend'), view='search:search_backend_reindex'
)


link_search_model_detail = Link(
    icon=icon_search_model_detail,
    kwargs={'search_model_name': 'resolved_object.full_name'},
    text=_(message='Fields'), view='search:search_model_detail'
)
link_search_model_list = Link(
    icon=icon_search_model_list, text=_(message='Search models'),
    view='search:search_model_list'
)
