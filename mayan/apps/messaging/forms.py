from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms
from mayan.apps.user_management.querysets import get_user_queryset

from .models import Message


class MessageCreateForm(forms.ModelForm):
    class Meta:
        fields = ('user', 'subject', 'body')
        model = Message

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs = {}
        self.fields['user'].queryset = get_user_queryset()
        self.fields['user'].widget.attrs = {'class': 'select2'}


class MessageDetailForm(forms.Form):
    body = form_fields.CharField(
        label=_(message='Body'),
        widget=form_widgets.TextAreaDiv(
            attrs={
                'class': 'scrollable views-text-wrap'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        self.fields['body'].initial = self.instance.body
