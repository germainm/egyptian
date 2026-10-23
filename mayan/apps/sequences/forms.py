from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.forms import FormDynamicModelBackend
from mayan.apps.forms import form_fields, forms

from .classes import SequenceBackend
from .models import Sequence


class SequenceBackendSelectionForm(forms.Form):
    backend = form_fields.ChoiceField(
        choices=(), help_text=_(
            message='The backend that will turn the position of the '
            'sequence into a value.'
        ), label=_(message='Backend')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['backend'].choices = SequenceBackend.get_choices()


class SequenceBackendDynamicForm(FormDynamicModelBackend):
    class Meta:
        fields = ('label', 'internal_name', 'on_limit', 'backend_data')
        model = Sequence


class SequenceResetForm(forms.Form):
    position = form_fields.IntegerField(
        help_text=_(
            message='Zero based counter of how many values have been '
            'consumed. To continue the numbering of a system being '
            'replaced, enter the number of values that system has already '
            'issued.'
        ), label=_(message='Position'), min_value=0
    )
