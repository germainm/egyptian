from django.urls import re_path

from mayan.apps.views.generics import SimpleView

from .api_views import APIThemeView, APIUserThemeView
from .views import CurrentUserThemeEditView, UserThemeEditView

urlpatterns_error_pages = [
    re_path(
        route=r'^errors/400/$', name='error_400', view=SimpleView.as_view(
            template_name='400.html'
        )
    ),
    re_path(
        route=r'^errors/403/$', name='error_403', view=SimpleView.as_view(
            template_name='403.html'
        )
    ),
    re_path(
        route=r'^errors/403/csrf/$', name='error_403_csrf',
        view=SimpleView.as_view(template_name='403_csrf.html')
    ),
    re_path(
        route=r'^errors/404/$', name='error_404', view=SimpleView.as_view(
            template_name='404.html'
        )
    ),
    re_path(
        route=r'^errors/500/$', name='error_500', view=SimpleView.as_view(
            template_name='500.html'
        )
    )
]

urlpatterns_theme = [
    re_path(
        route=r'^users/current/appearance/themes/$',
        name='user_current_theme_edit',
        view=CurrentUserThemeEditView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/themes/$', name='user_theme_edit',
        view=UserThemeEditView.as_view()
    )
]

urlpatterns = []
urlpatterns.extend(urlpatterns_error_pages)
urlpatterns.extend(urlpatterns_theme)

api_urls = [
    re_path(
        route=r'^users/current/themes/$',
        name='appearance-user-current-theme-detail',
        view=APIThemeView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/themes/$',
        name='appearance-user-theme-detail', view=APIUserThemeView.as_view()
    )
]
