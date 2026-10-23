from django.template import Library
from django.utils.safestring import mark_safe

from mayan.apps.common.serialization import yaml_dump

register = Library()


@register.filter(name='yaml_dump')
def tag_yaml_dump(value):
    """
    Converts the given value into a YAML-formatted string.
    """

    data = value.strip()

    result = yaml_dump(data=data).strip()

    result_safe = mark_safe(s=result)

    return result_safe
