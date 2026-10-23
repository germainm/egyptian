from collections import OrderedDict

from django.forms.widgets import *
from django.forms.widgets import __all__ as django_forms_widgets_all
from django.forms.widgets import (
    CheckboxSelectMultiple as DjangoCheckboxSelectMultiple, Media,
    RadioSelect as DjangoRadioSelect, SelectMultiple, TextInput, Widget
)
from django.utils.html import format_html

from .literals import (
    WIDGET_COLOR_ATTRIBUTE_AUTO_ENABLED, WIDGET_COLOR_ATTRIBUTE_AUTO_SOURCE,
    WIDGET_COLOR_NAME_SUFFIX_AUTO_STATE, WIDGET_COLOR_VALUE_FALSE,
    WIDGET_COLOR_VALUE_TRUE
)
from .settings import setting_color_auto_enabled

__all__ = django_forms_widgets_all + (
    'ColorWidget', 'DisableableSelectWidget', 'DropzoneWidget',
    'NamedMultiWidget', 'PlainWidget', 'TextAreaDiv'
)


class CheckboxSelectMultiple(DjangoCheckboxSelectMultiple):
    option_template_name = 'forms/forms/widgets/input_option.html'


class ColorWidget(TextInput):
    template_name = 'forms/forms/widgets/widget_color_picker.html'

    def __init__(self, attrs=None, auto_color_source_field_name=None):
        attrs = attrs or {}
        attrs['type'] = 'color'

        self.auto_color_source_field_name = auto_color_source_field_name

        self.auto_color_enabled_submitted = None

        super().__init__(attrs=attrs)

    def get_auto_color_state_name(self, name):
        return '{}{}'.format(name, WIDGET_COLOR_NAME_SUFFIX_AUTO_STATE)

    def get_auto_color_source_name(self, name):
        name_part_list = name.rsplit('-', 1)
        name_part_list[-1] = self.auto_color_source_field_name

        return '-'.join(name_part_list)

    def value_from_datadict(self, data, files, name):
        state_name = self.get_auto_color_state_name(name=name)

        if state_name in data:
            self.auto_color_enabled_submitted = data[
                state_name
            ] == WIDGET_COLOR_VALUE_TRUE

        return super().value_from_datadict(data=data, files=files, name=name)

    def get_context(self, name, value, attrs):
        context = super().get_context(attrs=attrs, name=name, value=value)

        if self.auto_color_source_field_name:
            source_name = self.get_auto_color_source_name(name=name)

            if self.auto_color_enabled_submitted is not None:
                auto_color_enabled = self.auto_color_enabled_submitted
            else:
                auto_color_enabled = setting_color_auto_enabled.value

            if auto_color_enabled:
                auto_color_enabled_text = WIDGET_COLOR_VALUE_TRUE
            else:
                auto_color_enabled_text = WIDGET_COLOR_VALUE_FALSE

            widget_context = context['widget']
            widget_context['auto_color_enabled'] = auto_color_enabled
            widget_context['auto_color_enabled_text'] = (
                auto_color_enabled_text
            )
            widget_context['auto_color_source_name'] = source_name
            widget_context['auto_color_state_name'] = (
                self.get_auto_color_state_name(name=name)
            )

            widget_attribute_dictionary = widget_context['attrs']
            widget_attribute_dictionary[
                WIDGET_COLOR_ATTRIBUTE_AUTO_ENABLED
            ] = auto_color_enabled_text
            widget_attribute_dictionary[
                WIDGET_COLOR_ATTRIBUTE_AUTO_SOURCE
            ] = source_name

        return context


class DisableableSelectWidget(SelectMultiple):
    def create_option(self, *args, **kwargs):
        result = super().create_option(*args, **kwargs)

        value = kwargs.get(
            'value', args[1]
        )

        if value in self.disabled_choices:
            result['attrs'].update(
                {'disabled': 'disabled'}
            )

        return result


class DropzoneWidget(Widget):
    template_name = 'forms/forms/widgets/dropzone.html'

    def id_for_label(self, id_):
        return ''


class NamedMultiWidget(Widget):
    subwidgets = None
    subwidgets_order = None
    template_name = 'django/forms/widgets/multiwidget.html'

    def __init__(self, attrs=None):
        self.widgets = {}
        for name, widget in OrderedDict(self.subwidgets).items():
            self.widgets[name] = widget() if isinstance(widget, type) else widget

        if not self.subwidgets_order:
            self.subwidgets_order = list(
                self.widgets.keys()
            )

        super().__init__(attrs)

    def _get_media(self):
        media = Media()
        for name, widget in self.widgets.items():
            media += widget.media
        return media
    media = property(_get_media)

    @property
    def is_hidden(self):
        return all(
            widget.is_hidden for name, widget in self.widgets.items()
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized

        value = self.decompress(value)

        final_attrs = context['widget']['attrs']
        input_type = final_attrs.pop('type', None)
        id_ = final_attrs.get('id')
        subwidgets = []

        _subwidgets_order = self.subwidgets_order.copy()
        for widget in self.widgets.keys():
            if widget not in _subwidgets_order:
                _subwidgets_order.append(widget)

        for subwidget_entry in _subwidgets_order:
            widget_name = subwidget_entry
            widget = self.widgets[widget_name]
            if input_type is not None:
                widget.input_type = input_type
            full_widget_name = '{}_{}'.format(name, widget_name)
            try:
                widget_value = value[widget_name]
            except IndexError:
                widget_value = None
            if id_:
                widget_attrs = final_attrs.copy()
                widget_attrs['id'] = '{}_{}'.format(id_, widget_name)
            else:
                widget_attrs = final_attrs
            subwidgets.append(
                widget.get_context(
                    full_widget_name, widget_value, widget_attrs
                )['widget']
            )
        context['widget']['subwidgets'] = subwidgets
        return context

    def id_for_label(self, id_):
        if id_:
            id_ += '_{}'.format(
                list(
                    self.widgets.keys()
                )[0]
            )
        return id_

    def value_from_datadict(self, data, files, name):
        return {
            name: widget.value_from_datadict(
                data, files, name + '_%s' % name
            ) for name, widget in self.widgets.items()
        }

    def value_omitted_from_data(self, data, files, name):
        return all(
            widget.value_omitted_from_data(data, files, name + '_%s' % name)
            for name, widget in self.widgets.items()
        )

    @property
    def needs_multipart_form(self):
        return any(
            widget.needs_multipart_form for name, widget in self.widgets.items()
        )


class PlainWidget(Widget):
    def id_for_label(self, id_):
        return ''

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value_final = ''
        else:
            value_final = value

        return format_html('{}', value_final)


class RadioSelect(DjangoRadioSelect):
    option_template_name = 'forms/forms/widgets/input_option.html'


class TextAreaDiv(Widget):
    template_name = 'appearance/forms/widgets/textareadiv.html'

    def id_for_label(self, id_):
        return ''
