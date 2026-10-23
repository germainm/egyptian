from django.apps import apps
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .literals import DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT


def is_user_locked(user):
    if not getattr(settings, 'AXES_ENABLED', True):
        return False

    from axes.helpers import get_cool_off

    AccessAttempt = apps.get_model(app_label='axes', model_name='AccessAttempt')

    username = user.get_username()
    queryset = AccessAttempt.objects.filter(username=username)

    cool_off = get_cool_off()
    if cool_off is not None:
        threshold = timezone.now() - cool_off
        queryset = queryset.filter(attempt_time__gte=threshold)

    failure_limit = getattr(
        settings, 'AXES_FAILURE_LIMIT',
        DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT
    )
    queryset_aggregate = queryset.aggregate(
        total=Sum('failures_since_start')
    )
    total = queryset_aggregate['total'] or 0

    is_locked = total >= failure_limit

    return is_locked


def reset_user_lockout(user):
    from axes.handlers.proxy import AxesProxyHandler

    username = user.get_username()

    access_attempts_removed = AxesProxyHandler.reset_attempts(
        username=username
    )

    return access_attempts_removed
