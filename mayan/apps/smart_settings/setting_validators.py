from collections.abc import Mapping

from django.contrib.auth.password_validation import (
    get_password_validators
)


def check_setting_is_list_of_mappings(raw_value, setting=None):
    if not isinstance(raw_value, (list, tuple)):
        raise ValueError(
            'the value must be a list, not a `{}`.'.format(
                type(raw_value).__name__
            )
        )

    for index, entry in enumerate(raw_value):
        if not isinstance(entry, Mapping):
            raise ValueError(
                'entry #{} must be a dictionary, not a `{}`.'.format(
                    index, type(entry).__name__
                )
            )

    return raw_value


def check_setting_is_list_of_strings(raw_value, setting=None):
    if not isinstance(raw_value, (list, tuple)):
        raise ValueError(
            'the value must be a list of strings, not a `{}`.'.format(
                type(raw_value).__name__
            )
        )

    for index, entry in enumerate(raw_value):
        if not isinstance(entry, str):
            raise ValueError(
                'entry #{} must be a string, not a `{}`.'.format(
                    index, type(entry).__name__
                )
            )

    return raw_value


def check_setting_secure_proxy_ssl_header(raw_value, setting=None):
    if raw_value is None:
        return raw_value

    if not isinstance(raw_value, (list, tuple)):
        raise ValueError(
            'the value must be null or a two item list of strings, not a '
            '`{}`.'.format(type(raw_value).__name__)
        )

    if len(raw_value) != 2:
        raise ValueError(
            'the value must contain exactly two items, the header name and '
            'the secure value.'
        )

    for index, entry in enumerate(raw_value):
        if not isinstance(entry, str):
            raise ValueError(
                'item #{} must be a string, not a `{}`.'.format(
                    index, type(entry).__name__
                )
            )

    return raw_value


def check_setting_auth_password_validators(raw_value, setting=None):
    try:
        get_password_validators(validator_config=raw_value)
    except Exception as exception:
        raise ValueError(
            'the value is not a usable list of password validators; '
            '{}'.format(exception)
        ) from exception

    return raw_value
