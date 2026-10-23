from math import isfinite

from django.core.exceptions import ImproperlyConfigured


def validation_function_check_renewal_interval(setting, raw_value):
    if not isfinite(raw_value):
        raise ImproperlyConfigured(
            'Setting `{}` must be a finite number of seconds; value is '
            '`{}`.'.format(setting.name, raw_value)
        )

    if raw_value <= 0:
        raise ImproperlyConfigured(
            'Setting `{}` must be a positive number of seconds; value is '
            '`{}`.'.format(setting.name, raw_value)
        )

    return raw_value
