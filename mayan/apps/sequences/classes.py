from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.classes import DynamicFormModelBackend

from .exceptions import SequenceBackendArgumentError


class SequenceBackend(DynamicFormModelBackend):
    _backend_app_label = 'sequences'
    _backend_model_name = 'Sequence'
    _loader_module_name = 'sequence_backends'

    form_fieldsets = (
        (
            _(message='General'), {
                'fields': ('label', 'internal_name', 'on_limit')
            }
        ),
    )

    def get_argument_integer(self, name, default=None):
        value = self.kwargs.get(name, default)

        if value is None or value == '':
            value = default

        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            raise SequenceBackendArgumentError(
                'Argument `{}` of backend `{}` must be an integer. '
                'Received: {}'.format(
                    name, self.backend_id, value
                )
            )

    def get_argument_integer_list(self, name):
        value = self.kwargs.get(name) or ''

        if isinstance(value, (list, tuple)):
            entry_list = value
        else:
            entry_list = value.split(',')

        result = []

        for entry in entry_list:
            entry = str(entry).strip()

            if not entry:
                continue

            try:
                result.append(
                    int(entry)
                )
            except ValueError:
                raise SequenceBackendArgumentError(
                    'Argument `{}` of backend `{}` must be a list of '
                    'integers. Received: {}'.format(
                        name, self.backend_id, value
                    )
                )

        if not result:
            raise SequenceBackendArgumentError(
                'Argument `{}` of backend `{}` must contain at least one '
                'integer.'.format(
                    name, self.backend_id
                )
            )

        return result

    def get_position_limit(self):
        return None

    def get_value(self, position):
        raise NotImplementedError

    def get_value_is_unique(self):
        return True


class SequenceBackendNull(SequenceBackend):
    label = _(message='Null backend')

    def get_value(self, position):
        return ''

    def get_value_is_unique(self):
        return False
