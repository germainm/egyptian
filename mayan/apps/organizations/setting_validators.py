import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

PATH_SEGMENT_REGULAR_EXPRESSION = re.compile(r'^[A-Za-z0-9._~+-]+$')


def validation_function_check_installation_url_format(setting, raw_value):
    if not raw_value:
        return raw_value

    cleaned_raw_value = raw_value.strip()

    if not cleaned_raw_value:
        return None

    split_result = urlsplit(url=cleaned_raw_value)

    if not split_result.scheme or not split_result.netloc:
        raise ValidationError(
            message=_(
                message='The installation URL must include a scheme and a '
                'host. Example: https://www.example.com:8080'
            )
        )

    if split_result.path or split_result.query or split_result.fragment:
        raise ValidationError(
            message=_(
                message='The installation URL must not include a path, query '
                'string or fragment. Use the ORGANIZATIONS_URL_BASE_PATH '
                'setting to specify the path.'
            )
        )

    return cleaned_raw_value


def validation_function_check_path_format(setting, raw_value):
    if not raw_value:
        return raw_value

    cleaned_raw_value = raw_value.strip()

    if not cleaned_raw_value:
        return None

    if cleaned_raw_value[0] == '/' or cleaned_raw_value[-1] == '/':
        raise ValidationError(
            message=_(
                message='The path value must not include a leading '
                'or trailing slash.'
            )
        )

    for segment in cleaned_raw_value.split('/'):
        if segment in ('', '.', '..') or not PATH_SEGMENT_REGULAR_EXPRESSION.match(segment):
            raise ValidationError(
                message=_(
                    message='The path value is not a valid URL path. Use one '
                    'or more path segments separated by single slashes. '
                    'Example: mayan-installations/home'
                )
            )

    return cleaned_raw_value
