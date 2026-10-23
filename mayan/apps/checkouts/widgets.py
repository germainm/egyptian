import datetime

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.literals import TIME_DELTA_UNIT_CHOICES
from mayan.apps.forms import form_widgets


class SplitTimeDeltaWidget(form_widgets.NamedMultiWidget):
    subwidgets = {
        'amount': form_widgets.NumberInput(
            attrs={
                'maxlength': 4, 'style': 'width: 8em;',
                'placeholder': _(message='Amount')
            }
        ),
        'unit': form_widgets.Select(
            attrs={'style': 'width: 8em;'}, choices=TIME_DELTA_UNIT_CHOICES
        )
    }

    def decompress(self, value):
        return {
            'amount': None, 'unit': None
        }

    def value_from_datadict(self, querydict, files, name):
        amount = querydict.get(
            '{}_amount'.format(name)
        )
        unit = querydict.get(
            '{}_unit'.format(name)
        )

        if not unit or not amount:
            return now()

        amount = int(amount)

        timedelta = datetime.timedelta(
            **{unit: amount}
        )
        return now() + timedelta
