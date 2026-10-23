from celery.schedules import crontab

from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.celery import app

from .renderers import (
    RendererChartJSDoughnut, RendererChartJSLine, RendererChartJSPie
)
from .queues import queue_task_execute_statistic, queue_statistics


class StatisticNamespace(AppsModuleLoaderMixin):
    _loader_module_name = 'statistics'
    _registry = {}

    @classmethod
    def get_all(cls):
        return list(
            cls._registry.values()
        )

    @classmethod
    def get(cls, slug):
        return cls._registry[slug]

    def __init__(self, slug, label):
        self.slug = slug
        self.label = label
        self._statistics = []
        self.__class__._registry[slug] = self

    def __str__(self):
        return str(self.label)

    def add_statistic(self, klass, *args, **kwargs):
        statistic = klass(*args, **kwargs)
        statistic.namespace = self
        self._statistics.append(statistic)

    @property
    def statistics(self):
        return self._statistics


StatisticNamespace.verbose_name = _(message='Statistics namespace')


class StatisticType:
    _registry = {}
    renderer = None

    @staticmethod
    def evaluate(data):
        try:
            for key, value in data.items():
                return {
                    key: StatisticType.evaluate(data=value)
                }
        except AttributeError:
            if type(data) is map:
                data = list(data)

        return data

    @staticmethod
    def purge_schedules():
        PeriodicTask = apps.get_model(
            app_label='django_celery_beat', model_name='PeriodicTask'
        )
        StatisticResult = apps.get_model(
            app_label='mayan_statistics', model_name='StatisticResult'
        )

        queryset = PeriodicTask.objects.filter(
            name__startswith='mayan_statistics.'
        ).exclude(
            name__in=StatisticType.get_task_names()
        )

        for periodic_task in queryset:
            crontab_instance = periodic_task.crontab
            periodic_task.delete()

            if crontab_instance and not crontab_instance.periodictask_set.all():
                crontab_instance.delete()

        StatisticResult.objects.filter(
            slug__in=queryset.values_list('name', flat=True)
        ).delete()

    @classmethod
    def get(cls, slug):
        return cls._registry[slug]

    @classmethod
    def get_all(cls):
        return list(
            cls._registry.values()
        )

    @classmethod
    def get_task_names(cls):
        return [
            task.get_task_name() for task in cls.get_all()
        ]

    def __init__(
        self, func, label, slug, day_of_month='*', day_of_week='*',
        hour='*', minute='*', month_of_year='*'
    ):
        self.slug = slug
        self.label = label
        self.func = func

        self.schedule = crontab(
            day_of_month=day_of_month, day_of_week=day_of_week, hour=hour,
            minute=minute, month_of_year=month_of_year
        )

        app.conf.beat_schedule.update(
            {
                self.get_task_name(): {
                    'task': queue_task_execute_statistic.dotted_path,
                    'schedule': self.schedule,
                    'args': (self.slug,)
                }
            }
        )

        app.conf.task_routes.update(
            {
                self.get_task_name(): {
                    'queue': queue_statistics.name
                }
            }
        )

        self.__class__._registry[slug] = self

    def __str__(self):
        return str(self.label)

    def execute(self):
        results = self.func()
        results = StatisticType.evaluate(data=results)
        self.store_results(results=results)

    def get_chart_context(self):
        return self.renderer(
            data=self.get_results_data()
        ).get_chart_context()

    def get_last_update(self):
        results = self.get_results()

        if results:
            return results.datetime
        else:
            return _(message='Never')

    def get_results(self, only=None):
        StatisticResult = apps.get_model(
            app_label='mayan_statistics', model_name='StatisticResult'
        )

        try:
            return StatisticResult.objects.get(slug=self.slug)
        except StatisticResult.DoesNotExist:
            return StatisticResult.objects.none()
        except StatisticResult.MultipleObjectsReturned:
            StatisticResult.objects.filter(slug=self.slug).delete()
            return StatisticResult.objects.none()

    def get_results_data(self):
        results = self.get_results()

        if results:
            return results.get_data()
        else:
            return {
                'series': {}
            }

    def get_task_name(self):
        return 'mayan_statistics.task_execute_statistic_{}'.format(self.slug)

    def store_results(self, results):
        StatisticResult = apps.get_model(
            app_label='mayan_statistics', model_name='StatisticResult'
        )

        StatisticResult.objects.filter(slug=self.slug).delete()

        statistic_result, created = StatisticResult.objects.get_or_create(
            slug=self.slug
        )
        statistic_result.store_data(data=results)


class StatisticTypeDoughnutChart(StatisticType):
    renderer = RendererChartJSDoughnut
    type_label = _(message='Doughnut chart')


class StatisticTypeLineChart(StatisticType):
    renderer = RendererChartJSLine
    type_label = _(message='Line chart')


class StatisticTypePieChart(StatisticType):
    renderer = RendererChartJSPie
    type_label = _(message='Pie chart')
