from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .literals import THROTTLING_PERIOD_MULTIPLIER_MAP


def validation_function_check_throttling_rate(setting, raw_value):
    if not raw_value:
        return raw_value

    cleaned_raw_value = raw_value.strip()

    if not cleaned_raw_value:
        return cleaned_raw_value

    try:
        count, period = cleaned_raw_value.split('/')
    except ValueError:
        raise ValidationError(
            message=_(
                message='The throttling rate must be expressed as '
                '`<number>/<period>`. Example: 10/second'
            )
        )

    try:
        int(count)
    except ValueError:
        raise ValidationError(
            message=_(
                message='The number of requests of the throttling rate '
                'must be an integer.'
            )
        )

    if period[0] not in THROTTLING_PERIOD_MULTIPLIER_MAP:
        raise ValidationError(
            message=_(
                message='The period of the throttling rate must start with '
                'one of the following: `s` (second), `m` (minute), `h` '
                '(hour), `d` (day).'
            )
        )

    return cleaned_raw_value
