from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_list_facet, menu_object, menu_return, menu_tools
)
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import StatisticNamespace, StatisticType
from .links import (
    link_statistic_namespace_detail, link_statistic_namespace_list,
    link_statistic_type_detail, link_statistic_type_queue, link_statistics
)


class StatisticsApp(MayanAppConfig):
    app_namespace = 'statistics'
    app_url = 'statistics'
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.mayan_statistics'
    static_media_ignore_patterns = (
        'statistics/node_modules/chart.js/book.*',
        'statistics/node_modules/chart.js/karma.conf.*',
        'statistics/node_modules/chart.js/samples/*',
        'statistics/node_modules/chart.js/src/*',
        'statistics/node_modules/chart.js/*docs*'
    )
    verbose_name = _(message='Statistics')

    def ready(self):
        super().ready()

        StatisticNamespace.load_modules()

        SourceColumn(
            attribute='type_label', include_label=True,
            label=_(message='Type'), source=StatisticType
        )

        SourceColumn(
            attribute='schedule',
            include_label=True, label=_(message='Schedule'),
            source=StatisticType
        )

        SourceColumn(
            attribute='get_last_update', include_label=True,
            label=_(message='Last update'), source=StatisticType
        )


        menu_list_facet.bind_links(
            links=(link_statistic_namespace_detail,),
            sources=(StatisticNamespace,)
        )

        menu_return.bind_links(
            links=(link_statistic_namespace_list,),
            sources=(
                StatisticNamespace, 'statistics:statistic_namespace_list'
            )
        )


        menu_list_facet.bind_links(
            links=(link_statistic_type_detail,), sources=(StatisticType,)
        )
        menu_object.bind_links(
            links=(link_statistic_type_queue,), sources=(StatisticType,)
        )

        menu_tools.bind_links(
            links=(link_statistics,)
        )
