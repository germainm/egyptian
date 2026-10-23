from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_sequence_value_store_name = RegexValidator(
    r'^[a-zA-Z][a-zA-Z0-9_]*\Z', _(
        "Enter a valid name consisting of letters, numbers, and "
        "underscores, and starting with a letter."
    ), 'invalid'
)
