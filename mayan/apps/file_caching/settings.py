from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_EVICTION_GRACE_PERIOD, DEFAULT_MAXIMUM_FAILED_PRUNE_ATTEMPTS,
    DEFAULT_MAXIMUM_NORMAL_PRUNE_ATTEMPTS
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='File caching'), name='file_caching'
)

setting_eviction_grace_period = setting_namespace.do_setting_add(
    default=DEFAULT_EVICTION_GRACE_PERIOD,
    global_name='FILE_CACHING_EVICTION_GRACE_PERIOD', help_text=_(
        message='Number of seconds during which a newly created cache file '
        'is protected from eviction, giving it time to be read at least '
        'once before it can be pruned to free up space. This keeps a '
        'freshly generated file from being deleted before its creator can '
        'use it, which would force a wasteful regeneration. The protection '
        'is skipped when every file in the cache is still within this '
        'window, so the cache can always be pruned below its maximum size. '
        'Set to 0 to disable.'
    )
)
setting_maximum_failed_prune_attempts = setting_namespace.do_setting_add(
    default=DEFAULT_MAXIMUM_FAILED_PRUNE_ATTEMPTS,
    global_name='FILE_CACHING_MAXIMUM_FAILED_PRUNE_ATTEMPTS', help_text=_(
        message='Number of times a cache will retry failed attempts to prune '
        'files to free up space for new a file being requested, before '
        'giving up.'
    )
)
setting_maximum_normal_prune_attempts = setting_namespace.do_setting_add(
    default=DEFAULT_MAXIMUM_NORMAL_PRUNE_ATTEMPTS,
    global_name='FILE_CACHING_MAXIMUM_NORMAL_PRUNE_ATTEMPTS', help_text=_(
        message='Number of times a cache will attempt to prune files to free '
        'up space for new a file being requested, before giving up.'
    )
)
