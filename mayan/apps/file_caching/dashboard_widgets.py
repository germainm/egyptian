from django.apps import apps
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.dashboards.classes import DashboardWidgetNumeric

from .icons import icon_file_caching
from .permissions import permission_cache_view


class DashboardWidgetFileCacheSizeAllocated(DashboardWidgetNumeric):
    icon = icon_file_caching
    label = _(message='Total cache allocated')
    link = reverse_lazy(viewname='file_caching:cache_list')

    def get_count(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        Cache = apps.get_model(
            app_label='file_caching', model_name='Cache'
        )

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_cache_view, user=self.request.user,
            queryset=Cache.objects.all()
        )

        total_size_allocated = queryset.aggregate(
            total_size=Sum('maximum_size')
        )['total_size'] or 0

        return format_lazy(
            '{}', filesizeformat(
                bytes_=total_size_allocated
            )
        )


class DashboardWidgetFileCacheSizeUsed(DashboardWidgetNumeric):
    icon = icon_file_caching
    label = _(message='Total cache used')
    link = reverse_lazy(viewname='file_caching:cache_list')

    def get_count(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        Cache = apps.get_model(
            app_label='file_caching', model_name='Cache'
        )

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_cache_view, user=self.request.user,
            queryset=Cache.objects.all()
        )

        total_size_allocated = queryset.aggregate(
            total_size=Sum('maximum_size')
        )['total_size'] or 1

        total_size_used = queryset.aggregate(
            total_size=Sum('partitions__files__file_size')
        )['total_size'] or 0

        return format_lazy(
            '{} ({:0.1f}%)', filesizeformat(
                bytes_=total_size_used
            ), total_size_used / total_size_allocated * 100
        )
