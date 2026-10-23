from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import (
    icon_statistic_detail, icon_statistic_namespace_detail,
    icon_statistic_namespace_list, icon_statistic_queue, icon_statistics
)
from .permissions import permission_statistics_view

link_statistic_namespace_detail = Link(
    args='resolved_object.slug', icon=icon_statistic_namespace_detail,
    permission=permission_statistics_view, text=_(message='Namespace details'),
    view='statistics:statistic_namespace_detail'
)
link_statistic_namespace_list = Link(
    icon=icon_statistic_namespace_list,
    permission=permission_statistics_view, text=_(message='Namespace list'),
    view='statistics:statistic_namespace_list'
)
link_statistic_type_queue = Link(
    args='resolved_object.slug', icon=icon_statistic_queue,
    permission=permission_statistics_view, text=_(message='Queue'),
    view='statistics:statistic_queue'
)
link_statistic_type_detail = Link(
    args='resolved_object.slug', icon=icon_statistic_detail,
    permission=permission_statistics_view, text=_(message='View'),
    view='statistics:statistic_detail'
)
link_statistics = Link(
    icon=icon_statistics, permission=permission_statistics_view,
    text=_(message='Statistics'), view='statistics:statistic_namespace_list'
)
