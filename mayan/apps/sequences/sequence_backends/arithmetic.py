from django.utils.translation import gettext_lazy as _

from ..classes import SequenceBackend
from ..exceptions import SequenceBackendArgumentError

from .literals import (
    DEFAULT_SEQUENCE_INCREMENT_LIST, DEFAULT_SEQUENCE_VALUE_FIRST,
    DEFAULT_SEQUENCE_WIDTH
)

__all__ = ('SequenceBackendArithmetic',)


class SequenceBackendArithmetic(SequenceBackend):
    form_fields = {
        'value_first': {
            'class': 'django.forms.IntegerField',
            'default': DEFAULT_SEQUENCE_VALUE_FIRST,
            'help_text': _(
                message='Value returned for the first position of the '
                'sequence.'
            ),
            'label': _(message='First value'), 'required': True
        },
        'increment_list': {
            'class': 'django.forms.CharField',
            'default': DEFAULT_SEQUENCE_INCREMENT_LIST,
            'help_text': _(
                message='Amount added to the value for each position '
                'consumed. A single amount is a constant step: "1" counts '
                'up by one, "5" by five, and "-1" counts down.'
            ),
            'label': _(message='Increments'), 'required': True
        },
        'value_limit': {
            'class': 'django.forms.IntegerField',
            'default': None,
            'help_text': _(
                message='Optional last value the sequence is allowed to '
                'return. The direction is taken from the increments, so '
                'this is a maximum for a sequence that climbs and a minimum '
                'for one that descends. The sequence is exhausted at the '
                'first value that passes it. Leave blank for an unbounded '
                'sequence.'
            ),
            'label': _(message='Value limit'), 'required': False
        },
        'width': {
            'class': 'django.forms.IntegerField',
            'default': DEFAULT_SEQUENCE_WIDTH,
            'help_text': _(
                message='Pad the value with leading zeros up to this many '
                'digits. A negative sign is not counted as a digit. Use 0 '
                'to disable padding.'
            ),
            'label': _(message='Width'), 'required': False
        }
    }
    label = _(message='Arithmetic')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Arithmetic'), {
                    'fields': (
                        'value_first', 'increment_list', 'value_limit',
                        'width'
                    )
                }
            ),
        )

        return fieldsets

    def get_increment_list(self):
        return self.get_argument_integer_list(name='increment_list')

    def get_position_limit(self):
        value_limit = self.get_argument_integer(name='value_limit')

        if value_limit is None:
            return None

        increment_list = self.get_increment_list()
        increment_total = sum(increment_list)

        if increment_total == 0:
            raise SequenceBackendArgumentError(
                'The increments of backend `{}` add up to zero, so the '
                'sequence has no direction of travel and can never pass a '
                'limit. Remove the value limit or change the '
                'increments.'.format(self.backend_id)
            )

        value_first = self.get_argument_integer(
            default=DEFAULT_SEQUENCE_VALUE_FIRST, name='value_first'
        )

        length = len(increment_list)
        result = None

        for cycle_remainder in range(length):
            prefix_sum = sum(
                increment_list[0:cycle_remainder]
            )

            cycle_count = (
                value_limit - value_first - prefix_sum
            ) // increment_total + 1

            position = max(cycle_count, 0) * length + cycle_remainder

            if result is None or position < result:
                result = position

        return result

    def get_value(self, position):
        increment_list = self.get_increment_list()
        value_first = self.get_argument_integer(
            default=DEFAULT_SEQUENCE_VALUE_FIRST, name='value_first'
        )
        width = self.get_argument_integer(default=0, name='width') or 0

        length = len(increment_list)

        cycle_count, cycle_remainder = divmod(position, length)

        value = value_first + cycle_count * sum(increment_list) + sum(
            increment_list[0:cycle_remainder]
        )

        return self.get_value_padded(value=value, width=width)

    def get_value_is_unique(self):
        increment_list = self.get_increment_list()

        increment_total = sum(increment_list)

        if increment_total == 0:
            return False

        residue_set = set()

        for cycle_remainder in range(
            len(increment_list)
        ):
            residue = sum(
                increment_list[0:cycle_remainder]
            ) % increment_total

            if residue in residue_set:
                return False

            residue_set.add(residue)

        return True

    def get_value_padded(self, value, width):
        if not width:
            return str(value)

        if value < 0:
            return '-{}'.format(
                str(-value).zfill(width)
            )

        return str(value).zfill(width)
