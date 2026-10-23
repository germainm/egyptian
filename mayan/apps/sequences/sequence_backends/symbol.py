from django.utils.translation import gettext_lazy as _

from ..classes import SequenceBackend
from ..exceptions import SequenceBackendArgumentError

from .literals import DEFAULT_SEQUENCE_SYMBOL_LIST

__all__ = ('SequenceBackendSymbol',)


class SequenceBackendSymbol(SequenceBackend):
    form_fields = {
        'symbol_list': {
            'class': 'django.forms.CharField',
            'default': DEFAULT_SEQUENCE_SYMBOL_LIST,
            'help_text': _(
                message='Ordered list of symbols to use, written one after '
                'another with nothing between them. A symbol that is not in '
                'this list can never be produced. Letters, digits, or any '
                'mix of them are equally valid.'
            ),
            'label': _(message='Symbols'), 'required': True
        },
        'repeat_maximum': {
            'class': 'django.forms.IntegerField', 'default': None,
            'help_text': _(
                message='How many times a symbol may be repeated before the '
                'sequence is considered exhausted. A value of 2 allows A to '
                'Z and then AA to ZZ. Leave blank for no limit.'
            ),
            'label': _(message='Maximum repeat'), 'required': False
        }
    }
    label = _(message='Symbol')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Symbols'), {
                    'fields': ('symbol_list', 'repeat_maximum')
                }
            ),
        )

        return fieldsets

    def get_position_limit(self):
        repeat_maximum = self.get_argument_integer(name='repeat_maximum')

        if repeat_maximum is None:
            return None

        return repeat_maximum * len(
            self.get_symbol_list()
        )

    def get_symbol_list(self):
        symbol_list = self.kwargs.get('symbol_list') or DEFAULT_SEQUENCE_SYMBOL_LIST

        if not symbol_list:
            raise SequenceBackendArgumentError(
                'The symbol list of backend `{}` cannot be empty.'.format(
                    self.backend_id
                )
            )

        return symbol_list

    def get_value_is_unique(self):
        symbol_list = self.get_symbol_list()

        return len(
            set(symbol_list)
        ) == len(symbol_list)

    def get_value(self, position):
        symbol_list = self.get_symbol_list()

        repeat_count, symbol_index = divmod(
            position, len(symbol_list)
        )

        return symbol_list[symbol_index] * (repeat_count + 1)
