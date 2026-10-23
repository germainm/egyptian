from django.template import Library

from ..classes import Dashboard

register = Library()


@register.simple_tag(name='dashboards_render_dashboard', takes_context=True)
def tag_dashboards_render_dashboard(context, name=None, stored_dashboard=None):
    if stored_dashboard is None:
        if not name:
            return ''

        try:
            dashboard = Dashboard.get(name=name)
        except KeyError:
            return ''

        stored_dashboard = dashboard.get_stored_dashboard()

    return stored_dashboard.render_for_user(request=context.request)
