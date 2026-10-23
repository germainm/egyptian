import json
import re

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

from .utils import parse_range


def _lazy_re_compile(regex, flags=0):
    def _compile():
        if isinstance(regex, str):
            return re.compile(regex, flags)
        else:
            assert not flags, 'flags must be empty if regex is passed pre-compiled'
            return regex
    return SimpleLazyObject(_compile)


@deconstructible
class JSONValidator:
    def __call__(self, value):
        value = value.strip()
        try:
            json.loads(s=value)
        except ValueError:
            raise ValidationError(
                code='invalid',
                message=_(message='Enter a valid JSON value.')
            )

    def __eq__(self, other):
        return (
            isinstance(other, JSONValidator)
        )

    def __ne__(self, other):
        return not (self == other)


@deconstructible
class YAMLValidator:
    def __call__(self, value):
        value = value.strip()
        try:
            yaml.load(stream=value, Loader=SafeLoader)
        except yaml.error.YAMLError:
            raise ValidationError(
                code='invalid',
                message=_(message='Enter a valid YAML value.')
            )

    def __eq__(self, other):
        return (
            isinstance(other, YAMLValidator)
        )

    def __ne__(self, other):
        return not (self == other)


@deconstructible
class RangeValidator:
    def __call__(self, value):
        value = value.strip()

        try:
            parse_range(range_string=value)
        except ValueError:
            raise ValidationError(
                code='invalid',
                message=_(
                    message='Enter a valid list of numbers. Separate the '
                    'entries with commas and use a dash for a range of '
                    'numbers. Example: 1,3,5-8'
                )
            )

    def __eq__(self, other):
        return (
            isinstance(other, RangeValidator)
        )

    def __ne__(self, other):
        return not (self == other)


internal_name_re = _lazy_re_compile(regex=r'^[a-zA-Z0-9_]+\Z')
validate_internal_name = RegexValidator(
    internal_name_re, _(
        "Enter a valid 'internal name' consisting of letters, numbers, and "
        "underscores."
    ), 'invalid'
)
