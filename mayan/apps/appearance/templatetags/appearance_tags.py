from django.apps import apps
from django.conf import settings
from django.template import Library
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _

from mayan.apps.views.template_cache_sources import TemplateCacheSourceRegistry

from ..classes import Theme
from ..exceptions import AppTemplateCacheStaleError
from ..literals import (
    CONTEXT_KEY_APP_TEMPLATE_CACHE_STATE, TAG_APP_TEMPLATE_CACHE_DISABLE
)
from ..settings import setting_app_template_cache_verify

app_templates_cache = {}
register = Library()


@register.filter(name='appearance_form_get_visile_fields_map')
def filter_appearance_form_get_visile_fields_map(form):
    field_map = {
        field.name: field for field in form.visible_fields()
    }
    return field_map


@register.filter(name='appearance_get_choice_value')
def filter_appearance_get_choice_value(field):
    try:
        return dict(field.field.choices)[
            field.value()
        ]
    except TypeError:
        return ', '.join(
            [
                subwidget.data['label'] for subwidget in field.subwidgets if subwidget.data['selected']
            ]
        )
    except KeyError:
        return _(message='None')


@register.filter(name='appearance_get_form_media_js')
def filter_appearance_get_form_media_js(form=None):
    if form:
        return [
            form.media.absolute_path(path) for path in form.media._js
        ]


@register.filter(name='appearance_object_list_count')
def filter_appearance_object_list_count(object_list):
    try:
        return object_list.count()
    except TypeError:
        return len(object_list)


def do_app_template_cache_verify(app, context, output_cached, template_name):
    """
    Render again an app template that was served from the cache and fail when
    the two results differ. A difference means the output depends on something
    the cache entry does not express, which outside of this check is not
    visible: the output of the first render is served for the life of the
    process.
    """
    output_fresh, cache_disabled = do_app_template_render(
        app=app, context=context, template_name=template_name
    )

    if output_fresh != output_cached:
        message = (
            'The app template "{}/app/{}.html" served from the app template '
            'cache does not match a fresh render of the same template. Its '
            'output depends on something the cache entry does not express. '
            'Add the "{}" tag to the template if the output varies per '
            'request, or register what the output depends on as a template '
            'cache source.'.format(
                app.label, template_name, TAG_APP_TEMPLATE_CACHE_DISABLE
            )
        )
        raise AppTemplateCacheStaleError(message)


def do_app_template_render(app, context, template_name):
    """
    Render the app template of an app. Returns the rendered output and
    whether the template disabled the caching of that output while it was
    rendered.
    """
    try:
        app_template = get_template(
            '{}/app/{}.html'.format(app.label, template_name)
        )
    except TemplateDoesNotExist:
        """
        Non fatal just means that the app did not defined an app
        template of this name and purpose.
        """
        return ('', False)
    else:
        app_template_cache_state = {'disabled': False}

        context_dictionary = context.flatten()
        context_dictionary[CONTEXT_KEY_APP_TEMPLATE_CACHE_STATE] = app_template_cache_state

        app_template_output = app_template.render(
            context=context_dictionary, request=context.get('request')
        )

        return (
            app_template_output, app_template_cache_state['disabled']
        )


@register.simple_tag(
    name='appearance_app_template_cache_disable', takes_context=True
)
def tag_appearance_app_template_cache_disable(context):
    """
    Keep the output of the app template being rendered out of the app
    template cache. Used by the app templates whose output varies per
    request, which no template cache source can express.

    The tag has to be reached on every render of the app template. A tag
    that is only reached for some renders lets the first render decide for
    the life of the process.
    """
    try:
        app_template_cache_state = context[
            CONTEXT_KEY_APP_TEMPLATE_CACHE_STATE
        ]
    except KeyError:
        """
        The template is being rendered outside of the app template tag,
        where there is no cache entry to disable.
        """
    else:
        app_template_cache_state['disabled'] = True

    return ''


@register.simple_tag(name='appearance_app_templates', takes_context=True)
def tag_appearance_app_templates(context, template_name):
    """
    Fetch the app templates for the requested `template_name`, render it with
    the current `request` from the `context`, and cache it for future use
    unless the template disabled the caching of its output. The cache entries
    are keyed by the active language. App templates contain translatable
    strings which are rendered in the language active during the request.

    App templates also render values that change while the process runs, like
    the settings. Each entry stores the token of the template cache sources it
    was rendered with and is only reused while that token is current, so a
    change of a source retires the entries rendered before it instead of being
    ignored until the next restart. The no caching tag remains the way to opt
    out for the templates whose output varies per request, which no source
    token can express.
    """
    result = []

    language = get_language() or settings.LANGUAGE_CODE
    template_cache_token = TemplateCacheSourceRegistry.get_template_cache_token()
    verify_enabled = setting_app_template_cache_verify.value

    for app in apps.get_app_configs():
        template_id = '{}.{}.{}'.format(app.label, template_name, language)

        cache_entry = app_templates_cache.get(template_id)

        cache_entry_usable = False

        if cache_entry is not None and not settings.DEBUG:
            cache_entry_usable = cache_entry['token'] == template_cache_token

        if cache_entry_usable:
            app_template_output = cache_entry['output']

            if verify_enabled:
                do_app_template_cache_verify(
                    app=app, context=context,
                    output_cached=app_template_output,
                    template_name=template_name
                )
        else:
            app_template_output, cache_disabled = do_app_template_render(
                app=app, context=context, template_name=template_name
            )

            if not cache_disabled:
                app_templates_cache[template_id] = {
                    'output': app_template_output,
                    'token': template_cache_token
                }

        result.append(app_template_output)

    return mark_safe(
        s=' '.join(result)
    )


@register.simple_tag(name='appearance_get_theme', takes_context=True)
def tag_appearance_get_theme(context):
    """
    Resolve the theme (frontend stylesheet) for the current request. Used by
    the frontend head template to emit the correct stylesheet link per user.
    """
    request = context.get('request')
    return Theme.get_for_request(request=request)
