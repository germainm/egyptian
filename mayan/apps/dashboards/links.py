from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import icon_dashboard_detail, icon_dashboard_list
from .permissions import permission_dashboard_view

link_dashboard_detail = Link(
    args='object.pk', icon=icon_dashboard_detail,
    permission=permission_dashboard_view, text=_(message='Details'),
    view='dashboards:dashboard_detail'
)
link_dashboard_list = Link(
    icon=icon_dashboard_list, text=_(message='Dashboards'),
    view='dashboards:dashboard_list'
)
