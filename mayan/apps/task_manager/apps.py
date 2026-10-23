import logging

from celery.backends.base import DisabledBackend

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import PROCESS_UPGRADE
from mayan.apps.app_manager.runlevels import runlevel_maintenance
from mayan.apps.common.menus import (
    menu_list_facet, menu_tools, menu_related, menu_return
)
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.celery import app as celery_app

from .classes import CeleryQueue, TaskType, Task, Worker
from .initializers import initializer_perform_upgrade
from .links import (
    link_queue_task_type_list, link_task_type_list, link_worker_list,
    link_worker_queue_list
)
from .literals import TEST_CELERY_RESULT_KEY, TEST_CELERY_RESULT_VALUE
from .methods import factory_method_periodic_task_save

logger = logging.getLogger(name=__name__)


class TaskManagerApp(MayanAppConfig):
    app_namespace = 'task_manager'
    app_url = 'task_manager'
    has_tests = True
    name = 'mayan.apps.task_manager'
    verbose_name = _(message='Task manager')

    def check_broker_connectivity(self):
        connection = celery_app.connection()

        logger.info('Starting Celery broker connectivity test')
        try:
            connection.ensure_connection(
                interval_step=0, interval_max=0, interval_start=0,
                timeout=0.1
            )
        except Exception as exception:
            logger.critical(
                'Failed to connect to the Celery broker at {}; {}'.format(
                    connection.as_uri(), exception
                )
            )
            raise
        else:
            connection.release()

    def check_results_backend_connectivity(self):
        backend = celery_app.backend

        if not isinstance(backend, DisabledBackend):
            retry_policy = backend.retry_policy

            backend.retry_policy = {
                'max_retries': 0, 'interval_start': 0, 'interval_step': 1,
                'interval_max': 1
            }

            logger.info('Starting Celery result backend connectivity test')
            try:
                backend.set(
                    key=TEST_CELERY_RESULT_KEY,
                    value=TEST_CELERY_RESULT_VALUE
                )
            except Exception as exception:
                logger.critical(
                    'Failed to connect to the Celery result backend at {}; {}'.format(
                        backend.as_uri(), exception
                    )
                )
                raise
            else:
                backend.delete(key=TEST_CELERY_RESULT_KEY)
                backend.retry_policy = retry_policy

    def ready(self):
        super().ready()

        PeriodicTask = apps.get_model(
            app_label='django_celery_beat', model_name='PeriodicTask'
        )

        try:
            self.check_broker_connectivity()
        except Exception as exception:
            print(
                'Error checking Celery broker connectivity: {}'.format(
                    exception
                )
            )
            exit(1)

        try:
            self.check_results_backend_connectivity()
        except Exception as exception:
            print(
                'Error checking Celery result backend connectivity: {}'.format(
                    exception
                )
            )
            exit(1)

        CeleryQueue.load_modules()

        if settings.DEBUG or settings.TESTING:
            PeriodicTask.add_to_class(
                name='save', value=factory_method_periodic_task_save(
                    super_save=PeriodicTask.save
                )
            )


        SourceColumn(
            attribute='label', is_identifier=True, label=_(message='Label'),
            source=CeleryQueue
        )
        SourceColumn(
            attribute='name', include_label=True, label=_(message='Name'),
            source=CeleryQueue
        )
        SourceColumn(
            attribute='default_queue', include_label=True,
            label=_(message='Default queue?'), source=CeleryQueue,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='transient', help_text=_(
                message='Transient queues are not persistent. Tasks in a '
                'transient queue are lost if the broker is restarted. '
                'Transient queues use less resources and managed non '
                'critical tasks.'
            ), include_label=True, label=_(message='Is transient?'),
            source=CeleryQueue, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_task_type_count', include_label=True,
            source=CeleryQueue
        )


        SourceColumn(attribute='get_label', source=TaskType)
        SourceColumn(
            attribute='get_dotted_path', include_label=True,
            is_identifier=True, source=TaskType
        )
        SourceColumn(
            attribute='get_schedule', include_label=True, source=TaskType
        )
        SourceColumn(
            attribute='get_deduplication_backend_label', include_label=True,
            source=TaskType
        )
        SourceColumn(
            attribute='get_queue', include_label=True,
            source=TaskType, widget=column_widgets.ObjectLinkWidget
        )
        SourceColumn(
            attribute='get_worker', include_label=True,
            source=TaskType, widget=column_widgets.ObjectLinkWidget
        )


        SourceColumn(
            attribute='task_type', include_label=True, label=_(
                message='Type'
            ), source=Task
        )
        SourceColumn(
            attribute='get_time_started', include_label=True,
            label=_(message='Start time'), source=Task
        )
        SourceColumn(
            func=lambda context: context['object'].kwargs['hostname'],
            include_label=True, label=_(message='Host'), source=Task
        )
        SourceColumn(
            func=lambda context: context['object'].kwargs['args'],
            include_label=True, label=_(message='Arguments'), source=Task
        )
        SourceColumn(
            func=lambda context: context['object'].kwargs['kwargs'],
            include_label=True, label=_(message='Keyword arguments'),
            source=Task
        )
        SourceColumn(
            func=lambda context: context['object'].kwargs['worker_pid'],
            include_label=True, label=_(message='Worker process ID'),
            source=Task
        )


        SourceColumn(
            attribute='label', is_identifier=True, label=_(message='Label'),
            source=Worker
        )
        SourceColumn(
            attribute='name', include_label=True, label=_(message='Name'),
            source=Worker
        )
        SourceColumn(
            attribute='default_worker', include_label=True,
            label=_(message='Default worker?'), source=Worker,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_maximum_memory_per_child', include_label=True,
            source=Worker
        )
        SourceColumn(
            attribute='maximum_tasks_per_child', help_text=_(
                message='Maximum number of tasks a worker can execute before '
                'it\'s replaced by a new process.'
            ), include_label=True, label=_(message='Maximum tasks per child'),
            source=Worker
        )
        SourceColumn(
            attribute='concurrency', help_text=_(
                message='The number of worker processes/threads to launch. '
                'Defaults to the number of CPUs available on the machine.'
            ), include_label=True, label=_(message='Concurrency'),
            source=Worker
        )
        SourceColumn(
            attribute='nice_level', help_text=_(
                message='The nice value determines the priority of the '
                'process. A higher value lowers the priority. The default '
                'value is 0.'
            ), include_label=True, label=_(message='Nice level'),
            source=Worker
        )
        SourceColumn(
            attribute='get_queue_count', include_label=True, source=Worker
        )
        SourceColumn(
            attribute='get_task_type_count', include_label=True,
            source=Worker
        )

        menu_list_facet.bind_links(
            links=(link_queue_task_type_list,), sources=(CeleryQueue,)
        )
        menu_list_facet.bind_links(
            links=(link_worker_queue_list,), sources=(Worker,)
        )

        menu_related.bind_links(
            links=(link_task_type_list,),
            sources=('task_manager:worker_list',)
        )
        menu_related.bind_links(
            links=(link_worker_list,),
            sources=('task_manager:task_type_list',)
        )

        menu_return.bind_links(
            links=(link_worker_list,),
            sources=(Worker, 'task_manager:worker_list')
        )

        menu_tools.bind_links(
            links=(link_task_type_list, link_worker_list,)
        )

        InitializationStep(
            function=initializer_perform_upgrade,
            label=_(message='Purge obsolete background tasks'),
            name='task_manager.perform_upgrade', process=PROCESS_UPGRADE,
            runlevel=runlevel_maintenance
        )
