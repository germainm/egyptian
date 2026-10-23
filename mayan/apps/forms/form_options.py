class FormOptions:
    def __init__(self, form, kwargs, options=None):
        for name, default_value in self.option_definitions.items():
            try:
                value = kwargs.pop(name)
            except KeyError:
                try:
                    value = getattr(
                        self, 'get_{}'.format(name)
                    )()
                except AttributeError:
                    try:
                        value = getattr(options, name)
                    except AttributeError:
                        value = default_value

            setattr(self, name, value)


class DetailFormOption(FormOptions):
    option_definitions = {
        'extra_fields': []
    }


class FilteredSelectionFormOptions(FormOptions):
    option_definitions = {
        'allow_multiple': False,
        'field_name': None,
        'help_text': None,
        'label': None,
        'model': None,
        'permission': None,
        'queryset': None,
        'required': True,
        'user': None,
        'widget_attributes': {'size': '10'},
        'widget_class': None
    }
