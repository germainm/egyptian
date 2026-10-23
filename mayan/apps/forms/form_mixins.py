import types

from django import forms as django_forms
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class FormMixinFilteredFieldsReload:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_fields_reload(self):
        field_reload_attributes = self.get_field_reload_attributes()

        for field_name in self.fields:
            field_instance = self.fields[field_name]
            if hasattr(field_instance, 'reload'):
                for key, value in field_reload_attributes.items():
                    setattr(field_instance, key, value)

                field_instance.reload()

    def get_field_reload_attributes(self):
        return {}


class FormMixinDynamicFields(FormMixinFilteredFieldsReload):
    def __init__(self, schema, *args, **kwargs):
        self.schema = schema

        super().__init__(*args, **kwargs)

        self.fieldsets = self.schema.get(
            'fieldsets', ()
        )
        self.fieldset_exclude_list = self.schema.get(
            'fieldset_exclude_list', ()
        )

        widgets = self.schema.get(
            'widgets', {}
        )

        field_order = self.get_field_order()

        for field_name in field_order:
            field_data = self.schema['fields'][field_name]
            field_class = import_string(
                dotted_path=field_data['class']
            )
            kwargs = {
                'label': field_data['label'],
                'required': field_data.get('required', True),
                'initial': field_data.get('default', None),
                'help_text': field_data.get('help_text')
            }

            widget = widgets.get(field_name)
            if widget:
                kwargs['widget'] = import_string(
                    dotted_path=widget['class']
                )(
                    **widget.get(
                        'kwargs', {}
                    )
                )

            kwargs.update(
                field_data.get(
                    'kwargs', {}
                )
            )
            self.fields[field_name] = field_class(**kwargs)

    def get_field_order(self):
        return self.schema.get(
            'field_order', self.schema['fields'].keys()
        )

    @property
    def media(self):
        media = super().media
        media += django_forms.Media(
            **self.schema.get(
                'media', {}
            )
        )
        return media


class FormMixinFormMeta:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._form_meta = self._get_form_meta()

    def _get_form_meta(self, options_class_name='FormMeta'):
        merged = {}

        lineage = reversed(
            type(self).mro()
        )

        for base in lineage:
            options = getattr(base, options_class_name, None)
            if options:
                for name in dir(options):
                    if not name.startswith('_'):
                        merged[name] = getattr(options, name)

        return types.SimpleNamespace(**merged)


class FormMixinFieldsets(FormMixinFormMeta):
    fieldset_exclude_list = None
    fieldsets = None

    def get_fieldset_exclude_list(self):
        return self.fieldset_exclude_list or ()

    def get_fieldsets(self):
        fieldsets = getattr(self._form_meta, 'fieldsets', self.fieldsets)

        if fieldsets:
            fieldsets_field_list = []
            for fieldset, data in fieldsets:
                fieldsets_field_list.extend(
                    data['fields']
                )

            set_fields = set(self.fields)
            set_fieldsets = set(fieldsets_field_list)

            fieldset_exclude_list = self.get_fieldset_exclude_list()

            if fieldset_exclude_list:
                set_fields -= set(fieldset_exclude_list)
                set_fieldsets -= set(fieldset_exclude_list)

            if set_fields != set_fieldsets:
                raise ImproperlyConfigured(
                    'Mismatch fieldset fields: `{fields}` in form `{form}`'.format(
                        fields=', '.join(
                            set_fields.symmetric_difference(set_fieldsets)
                        ), form=self.__class__.__name__
                    )
                )

            return fieldsets
        else:
            return (
                (
                    None, {
                        'fields': tuple(self.fields)
                    }
                ),
            )
