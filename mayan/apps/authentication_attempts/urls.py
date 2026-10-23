from django.urls import re_path

from .api_views import (
    APICurrentUserLoginAttemptListView, APILoginAttemptDetailView,
    APILoginAttemptListView, APIUserLoginAttemptListView
)
from .views import (
    CurrentUserLoginAttemptListView, LoginAttemptListView,
    UserLoginAttemptListView
)

urlpatterns = [
    re_path(
        route=r'^login_attempts/$', name='login_attempt_list',
        view=LoginAttemptListView.as_view()
    ),
    re_path(
        route=r'^users/current/login_attempts/$',
        name='user_current_login_attempt_list',
        view=CurrentUserLoginAttemptListView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/login_attempts/$',
        name='user_login_attempt_list',
        view=UserLoginAttemptListView.as_view()
    )
]

api_urls = [
    re_path(
        route=r'^login_attempts/$', name='login_attempt-list',
        view=APILoginAttemptListView.as_view()
    ),
    re_path(
        route=r'^login_attempts/(?P<login_attempt_id>[0-9]+)/$',
        name='login_attempt-detail',
        view=APILoginAttemptDetailView.as_view()
    ),
    re_path(
        route=r'^user/current/login_attempts/$',
        name='user_current-login_attempt-list',
        view=APICurrentUserLoginAttemptListView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/login_attempts/$',
        name='user-login_attempt-list',
        view=APIUserLoginAttemptListView.as_view()
    )
]
