from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from ..literals import PAGE_RANGE_ALL, PAGE_RANGE_CHOICES


class PrintForm(forms.Form):
    page_group = form_fields.ChoiceField(
        choices=PAGE_RANGE_CHOICES, initial=PAGE_RANGE_ALL,
        label=_(message='Page group'), widget=form_widgets.RadioSelect
    )
    page_range = form_fields.CharField(
        help_text=_(
            message='Page numbers or page ranges separated by commas. '
            'Example: 1,3,5-8'
        ), label=_(message='Page range'), required=False
    )


class PageNumberForm(forms.Form):
    page = form_fields.ModelChoiceField(
        help_text=_(
            message='Page number from which all the transformations will be '
            'cloned. Existing transformations will be lost.'
        ), queryset=None
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super().__init__(*args, **kwargs)
        self.fields['page'].queryset = self.instance.pages.all()
