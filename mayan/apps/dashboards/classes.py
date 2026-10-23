from django.apps import apps
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.utils import OperationalError, ProgrammingError
from django.template import loader
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin

from .icons import (
    icon_dashboard_link_icon, icon_dashboard_widget_list_empty
)


class Dashboard(AppsModuleLoaderMixin):
    _loader_module_name = 'dashboards'
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_all(cls):
        return sorted(
            cls._registry.values(), key=lambda x: x.label
        )

    @classmethod
    def post_load_modules(cls):
        StoredDashboard = apps.get_model(
            app_label='dashboards', model_name='StoredDashboard'
        )

        try:
            StoredDashboard.objects.refresh()
        except (OperationalError, ProgrammingError):
            """
            Non fatal. Non initialized installation. Ignore exception.
            """

    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.stored_dashboard = None
        self.widgets = {}
        self.removed_widgets = []
        self.__class__._registry[name] = self

    def add_widget(self, widget, order=0):
        self.widgets[widget] = {'widget': widget, 'order': order}

    def get_stored_dashboard(self):
        if self.stored_dashboard is None:
            StoredDashboard = apps.get_model(
                app_label='dashboards', model_name='StoredDashboard'
            )

            self.stored_dashboard, created = StoredDashboard.objects.get_or_create(
                name=self.name
            )

        return self.stored_dashboard

    def get_widget_count(self):
        return len(self.widgets)

    def get_widgets(self):
        return map(
            lambda x: x['widget'],
            filter(
                lambda x: x['widget'] not in self.removed_widgets,
                sorted(
                    self.widgets.values(),
                    key=lambda x: (
                        x['order'], x['widget'].label
                    )
                )
            )
        )

    def remove_widget(self, widget):
        self.removed_widgets.append(widget)

    def render(self, request):
        rendered_widgets = [
            widget().render(request=request) for widget in self.get_widgets()
        ]

        return loader.render_to_string(
            template_name='dashboards/dashboard.html', context={
                'dashboard': self, 'widgets': rendered_widgets
            }
        )


class BaseDashboardWidget:
    _registry = {}
    context = {}
    template_name = None

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_all(cls):
        return cls._registry.items()

    @classmethod
    def register(cls, klass):
        cls._registry[klass.name] = klass

    def get_base_context(self):
        raise NotImplementedError

    def get_context(self):
        return {}

    def render(self, request):
        self.request = request
        context = self.get_base_context()
        context.update(
            self.get_context()
        )
        context.update(
            {'request': request}
        )

        if self.template_name:
            return loader.render_to_string(
                context=context, template_name=self.template_name
            )


class DashboardWidgetNumeric(BaseDashboardWidget):
    count = 0
    icon = None
    label = None
    link = None
    link_icon = icon_dashboard_link_icon
    template_name = 'dashboards/numeric_widget.html'

    def get_base_context(self):
        return {
            'count': intcomma(
                value=self.get_count()
            ),
            'count_raw': self.count,
            'icon': self.icon,
            'label': self.label,
            'link': self.link,
            'link_icon': self.link_icon
        }


class DashboardWidgetList(BaseDashboardWidget):
    columns = None
    empty_icon = icon_dashboard_widget_list_empty
    empty_link_navigation = None
    empty_link_text = None
    empty_link_url = None
    empty_text = _(message='There is no data to display.')
    icon = None
    label = None
    link = None
    link_icon = icon_dashboard_link_icon
    object_list_length = 10
    template_name = 'dashboards/widget_list.html'

    def get_base_context(self):
        queryset = self.get_object_list()
        object_list = queryset[:self.object_list_length]

        return {
            'columns': self.columns or (),
            'empty_icon': self.empty_icon,
            'empty_link': self.get_empty_link(),
            'empty_text': self.empty_text,
            'object_list': object_list,
            'icon': self.icon,
            'label': self.label,
            'link': self.link,
            'link_icon': self.link_icon
        }

    def get_empty_link(self):
        navigation_link = self.empty_link_navigation

        if navigation_link:
            resolved_link = navigation_link.resolve(request=self.request)

            if resolved_link:
                return {
                    'text': resolved_link.text, 'url': resolved_link.url
                }

        if self.empty_link_url and self.empty_link_text:
            return {
                'text': self.empty_link_text, 'url': self.empty_link_url
            }

        return None
