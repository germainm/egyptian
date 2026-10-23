from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validation_function_integer_minimum_one(setting, raw_value):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValidationError(
            message=_(message='The value must be an integer.')
        )

    if value < 1:
        raise ValidationError(
            message=_(
                message='The value must be an integer of 1 or greater.'
            )
        )

    return raw_value


def validation_function_integer_minimum_zero(setting, raw_value):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValidationError(
            message=_(message='The value must be an integer.')
        )

    if value < 0:
        raise ValidationError(
            message=_(
                message='The value must be an integer of 0 or greater.'
            )
        )

    return raw_value
