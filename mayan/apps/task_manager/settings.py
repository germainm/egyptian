from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster
from mayan.apps.smart_settings.utils import get_environment_variable_full_name

from .literals import (
    DEFAULT_CELERY_APP_CLASS, DEFAULT_CELERY_BROKER_LOGIN_METHOD,
    DEFAULT_CELERY_BROKER_URL, DEFAULT_CELERY_BROKER_USE_SSL,
    DEFAULT_CELERY_RESULT_BACKEND,
    DEFAULT_TASK_MANAGER_DEDUPLICATION_BACKEND_MAP,
    DEFAULT_TASK_MANAGER_DEDUPLICATION_QUEUED_INTERVAL,
    DEFAULT_TASK_MANAGER_DEDUPLICATION_STALE_INTERVAL
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Celery'), name='celery'
)
setting_namespace_task_manager = setting_cluster.do_namespace_add(
    label=_(message='Task manager'), name='task_manager'
)

setting_deduplication_backend_map = setting_namespace_task_manager.do_setting_add(
    default=DEFAULT_TASK_MANAGER_DEDUPLICATION_BACKEND_MAP,
    global_name='TASK_MANAGER_DEDUPLICATION_BACKEND_MAP', help_text=_(
        message='Deduplication strategy to use for a task type, overriding '
        'the one the app owning the task declared. A mapping of the dotted '
        'path of a task type to the dotted path of a strategy class. A task '
        'type that is not named keeps the strategy it declares. Use it to '
        'turn deduplication off for a task type that misbehaves, by '
        'mapping it to `TaskDeduplicationBackendNull`, and to compare the '
        'strategies on one installation without rebuilding it.'
    )
)
setting_deduplication_queued_interval = setting_namespace_task_manager.do_setting_add(
    data_type=int,
    default=DEFAULT_TASK_MANAGER_DEDUPLICATION_QUEUED_INTERVAL,
    global_name='TASK_MANAGER_DEDUPLICATION_QUEUED_INTERVAL', help_text=_(
        message='Time in seconds after which the marker of a deduplicated '
        'task whose work has not begun stops suppressing new requests for '
        'that work. It covers the wait in the queue, so a value below the '
        'longest wait a deployment produces makes a task that is merely '
        'queued be dispatched a second time, which is most likely exactly '
        'when the installation is already behind. It is also what allows '
        'work to resume without intervention when a worker ends between '
        'the moment the marker is stored and the moment the task is '
        'published, so the value is an upper bound on how long that work '
        'can remain undone.'
    )
)
setting_deduplication_stale_interval = setting_namespace_task_manager.do_setting_add(
    data_type=int,
    default=DEFAULT_TASK_MANAGER_DEDUPLICATION_STALE_INTERVAL,
    global_name='TASK_MANAGER_DEDUPLICATION_STALE_INTERVAL', help_text=_(
        message='Time in seconds after which the marker of a deduplicated '
        'task whose work has begun stops suppressing new requests for that '
        'work. It covers the execution alone, so it can be sized to how '
        'long the work itself takes. This is what allows work to resume '
        'without intervention when a worker ends in the middle of it.'
    )
)

celery_app_class_environment_variable_name = get_environment_variable_full_name(
    name='CELERY_CLASS'
)
setting_celery_app_class = setting_namespace.do_setting_add(
    default=DEFAULT_CELERY_APP_CLASS,
    global_name=celery_app_class_environment_variable_name,
    help_text=_(
        message='The class used to instantiate the main Celery app.'
    )
)
setting_celery_broker_login_method = setting_namespace.do_setting_add(
    default=DEFAULT_CELERY_BROKER_LOGIN_METHOD,
    global_name='CELERY_BROKER_LOGIN_METHOD', help_text=_(
        message='Default: "AMQPLAIN". Set custom amqp login method.'
    )
)
setting_celery_broker_url = setting_namespace.do_setting_add(
    default=DEFAULT_CELERY_BROKER_URL, global_name='CELERY_BROKER_URL',
    help_text=_(
        message='Default: "amqp://". Default broker URL. This must be a URL '
        'in the form of: '
        'transport://userid:password@hostname:port/virtual_host Only the '
        'scheme part (transport://) is required, the rest is optional, and '
        'defaults to the specific transports default values.'
    )
)
setting_celery_broker_use_ssl = setting_namespace.do_setting_add(
    default=DEFAULT_CELERY_BROKER_USE_SSL,
    global_name='CELERY_BROKER_USE_SSL', help_text=_(
        message='Default: "Disabled". Toggles SSL usage on broker connection '
        'and SSL settings. The valid values for this option vary by '
        'transport.'
    )
)
setting_celery_result_backend = setting_namespace.do_setting_add(
    default=DEFAULT_CELERY_RESULT_BACKEND,
    global_name='CELERY_RESULT_BACKEND', help_text=_(
        message='Default: No result backend enabled by default. The backend '
        'used to store task results (tombstones). Refer to '
        'http://docs.celeryproject.org/en/v4.1.0/userguide/configuration.'
        'html#result-backend'
    )
)
