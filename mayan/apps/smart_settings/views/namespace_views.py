from django.http import Http404
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.literals import LIST_MODE_CHOICE_ITEM
from mayan.apps.views.generics import SingleObjectListView

from ..icons import (
    icon_setting_cluster_namespace_list, icon_setting_namespace_detail
)
from ..permissions import permission_settings_view
from ..setting_clusters import setting_cluster


class SettingNamespaceDetailView(SingleObjectListView):
    view_icon = icon_setting_namespace_detail
    view_permission = permission_settings_view
    list_mode_fixed = LIST_MODE_CHOICE_ITEM

    def get_extra_context(self):
        namespace = self.get_namespace()

        return {
            'column_class': 'col-12',
            'hide_object': True,
            'no_results_icon': icon_setting_namespace_detail,
            'no_results_text': _(
                message='Settings control the configurable behavior of the '
                'app that owns this namespace.'
            ),
            'no_results_title': _(message='No settings available'),
            'object': namespace,
            'panel_item_template': 'smart_settings/widgets/setting_panel.html',
            'subtitle': _(
                message='Settings inherited from an environment variable '
                'take precedence and cannot be changed in this view. '
            ),
            'title': _(message='Settings in namespace: %s') % namespace
        }

    def get_namespace(self):
        try:
            return setting_cluster.get_namespace(
                name=self.kwargs['namespace_name']
            )
        except KeyError:
            raise Http404(
                _(message='Namespace: %s, not found') % self.kwargs[
                    'namespace_name'
                ]
            )

    def get_source_queryset(self):
        setting_namespace = self.get_namespace()
        return setting_namespace.get_setting_list()


class SettingNamespaceListView(SingleObjectListView):
    extra_context = {
        'hide_link': True,
        'no_results_icon': icon_setting_cluster_namespace_list,
        'no_results_text': _(
            message='Setting namespaces group the configuration options '
            'of each app.'
        ),
        'no_results_title': _(message='No setting namespaces available'),
        'title': _(message='Setting namespaces')
    }
    view_icon = icon_setting_cluster_namespace_list
    view_permission = permission_settings_view

    def get_source_queryset(self):
        return setting_cluster.get_namespace_list()
