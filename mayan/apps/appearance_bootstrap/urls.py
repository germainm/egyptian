from django.urls import re_path

from .api_views import APIColorModeView, APIUserColorModeView
from .views import CurrentUserColorModeEditView, UserColorModeEditView

urlpatterns = [
    re_path(
        route=r'^users/current/color_modes/$',
        name='user_current_color_mode_edit',
        view=CurrentUserColorModeEditView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/color_modes/$',
        name='user_color_mode_edit',
        view=UserColorModeEditView.as_view()
    )
]

api_urls = [
    re_path(
        route=r'^users/current/color_modes/$',
        name='bootstrap-current_user-color_mode-detail',
        view=APIColorModeView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/color_modes/$',
        name='bootstrap-user-color_mode-detail',
        view=APIUserColorModeView.as_view()
    )
]
