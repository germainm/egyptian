from django.core.exceptions import ImproperlyConfigured


class DynamicFormBackendMixin:
    form_field_widgets = {}
    form_fields = {}
    form_fieldset_exclude_list = ('backend_data',)
    form_media = {}

    @classmethod
    def do_sanity_check(cls, attribute, name):
        super_attribute = getattr(
            cls, name, {}
        )

        if id(super_attribute) == id(attribute):
            raise ImproperlyConfigured(
                'Don\'t update the form `{}` dictionary `{}` directly. '
                'Instead copy the dictionary.'.format(cls, name)
            )

    @classmethod
    def get_form_field_order(cls):
        return getattr(
            cls, 'form_field_order', ()
        )

    @classmethod
    def get_form_field_widgets(cls):
        form_field_widgets = getattr(
            cls, 'form_field_widgets', {}
        )

        form_field_widgets_copy = form_field_widgets.copy()

        return form_field_widgets_copy

    @classmethod
    def get_form_fields(cls):
        form_fields = getattr(
            cls, 'form_fields', {}
        )
        form_fields_copy = form_fields.copy()

        return form_fields_copy

    @classmethod
    def get_form_fieldset_exclude_list(cls):
        return getattr(
            cls, 'form_fieldset_exclude_list', ()
        )

    @classmethod
    def get_form_fieldsets(cls):
        return getattr(
            cls, 'form_fieldsets', ()
        )

    @classmethod
    def get_form_media(cls):
        form_media = getattr(
            cls, 'form_media', {}
        )
        form_media_copy = form_media.copy()

        return form_media_copy

    @classmethod
    def get_form_schema(cls, *args, **kwargs):
        form_fields = cls.get_form_fields(**kwargs)
        form_fieldset_exclude_list = cls.get_form_fieldset_exclude_list(**kwargs)
        form_fieldsets = cls.get_form_fieldsets(**kwargs)
        form_media = cls.get_form_media()
        form_field_widgets = cls.get_form_field_widgets(**kwargs)

        result = {
            'fields': form_fields,
            'fieldset_exclude_list': form_fieldset_exclude_list,
            'fieldsets': form_fieldsets,
            'media': form_media,
            'widgets': form_field_widgets
        }

        form_field_order = cls.get_form_field_order(**kwargs) or tuple(
            form_fields.keys()
        )

        result['field_order'] = form_field_order

        cls.do_sanity_check(attribute=form_fields, name='form_fields')
        cls.do_sanity_check(attribute=form_media, name='form_media')
        cls.do_sanity_check(
            attribute=form_field_widgets, name='form_field_widgets'
        )

        return result
