import json

from django.db.models import Model
from django.db.models.query import QuerySet

from mayan.apps.forms import form_widgets, forms


class BackendDynamicFormMetaclass(forms.ModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(BackendDynamicFormMetaclass, mcs).__new__(
            mcs=mcs, name=name, bases=bases, attrs=attrs
        )

        if new_class._meta.fields:
            new_class._meta.fields += ('backend_data',)
            widgets = getattr(
                new_class._meta, 'widgets', {}
            ) or {}
            widgets['backend_data'] = form_widgets.HiddenInput
            new_class._meta.widgets = widgets

        return new_class


class FormDynamicModelBackend(
    forms.DynamicModelForm, metaclass=BackendDynamicFormMetaclass
):
    widgets = {'backend_data': form_widgets.HiddenInput}

    def __init__(self, backend_path=None, user=None, *args, **kwargs):
        self.backend_path = backend_path
        self.user = user

        super().__init__(*args, **kwargs)

        backend_data = self.instance.get_backend_data()

        if backend_data:
            for field_name in self.get_backend_fields():
                self.fields[field_name].initial = backend_data.get(
                    field_name, None
                )

        self.do_fields_reload()

    def clean(self):
        data = super().clean()

        backend_data = {}

        for field_name, field_data in self.schema['fields'].items():
            backend_data[field_name] = data.pop(
                field_name, field_data.get('default', None)
            )
            if isinstance(backend_data[field_name], QuerySet):
                backend_data[field_name] = list(
                    backend_data[field_name].values_list('id', flat=True)
                )
            elif isinstance(backend_data[field_name], Model):
                backend_data[field_name] = backend_data[field_name].pk

        data['backend_data'] = json.dumps(obj=backend_data)

        return data

    def get_backend_fields(self):
        backend_class = self.instance.get_backend_class()
        return backend_class.get_form_fields()

    def get_field_reload_attributes(self):
        return {'user': self.user}
