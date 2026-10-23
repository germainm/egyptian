import json

from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from .classes import QuotaBackend
from .models import Quota


class QuotaBackendSelectionForm(forms.Form):
    backend = form_fields.ChoiceField(
        choices=(), label=_(message='Backend'), help_text=_(
            message='The quota driver for this entry.'
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['backend'].choices = QuotaBackend.get_choices()


class QuotaDynamicForm(forms.DynamicModelForm):
    class Meta:
        fields = ('enabled', 'backend_data')
        model = Quota
        widgets = {'backend_data': form_widgets.HiddenInput}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop(
            'user', {}
        )
        result = super().__init__(*args, **kwargs)

        self.do_fields_reload()

        if self.instance.backend_data:
            for key, value in json.loads(s=self.instance.backend_data).items():
                self.fields[key].initial = value

        return result

    def clean(self):
        data = super().clean()
        backend_data = {}

        for field_name, field_data in self.schema['fields'].items():
            field_data = data.pop(
                field_name, field_data.get('default', None)
            )

            if isinstance(field_data, models.Model):
                field_data = field_data.pk

            if isinstance(field_data, models.query.QuerySet):
                field_data = list(
                    field_data.values_list('pk', flat=True)
                )

            backend_data[field_name] = field_data

        data['backend_data'] = json.dumps(obj=backend_data)
        return data

    def get_field_reload_attributes(self):
        return {'user': self.user}
