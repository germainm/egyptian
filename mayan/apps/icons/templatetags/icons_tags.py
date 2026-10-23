from django.template import Library
from django.utils.module_loading import import_string

register = Library()


def get_render_kwargs(kwargs):
    render_kwargs = {}

    for key, value in kwargs.items():
        if '__' in key:
            subdictionary = render_kwargs
            parts = key.split('__')
            for part in parts:
                subdictionary.setdefault(
                    part, {}
                )
                dictionary_pointer = subdictionary
                subdictionary = subdictionary[part]

            dictionary_pointer[part] = value
        else:
            render_kwargs[key] = value

    return render_kwargs


@register.simple_tag(name='icons_get_icon')
def tag_icons_get_icon(icon_path, **kwargs):
    icon = import_string(dotted_path=icon_path)

    return icon.render(
        **get_render_kwargs(kwargs=kwargs)
    )


@register.simple_tag(name='icons_icon_render')
def tag_icons_icon_render(icon, enable_shadow=False, **kwargs):
    render_kwargs = get_render_kwargs(kwargs=kwargs)
    render_kwargs.setdefault(
        'extra_context', {}
    )
    render_kwargs['extra_context']['enable_shadow'] = enable_shadow

    return icon.render(**render_kwargs)
