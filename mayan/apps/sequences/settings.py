from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import DEFAULT_SEQUENCE_VALUE_COUNT_MAXIMUM

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Sequences'), name='sequences'
)

setting_value_count_maximum = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_SEQUENCE_VALUE_COUNT_MAXIMUM,
    global_name='SEQUENCES_VALUE_COUNT_MAXIMUM', help_text=_(
        message='Upper bound for the number of values a single call may '
        'reserve from a sequence. One value is produced for each reserved '
        'position, so this is what bounds the memory of a call. The size of '
        'the position itself has no bearing on the cost, therefore this '
        'limits neither how far a sequence may advance nor how many values '
        'it may issue in total.'
    )
)
