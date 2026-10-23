from django.urls import path, re_path

from .views.authentication_views import (
    MayanLoginView, MayanLogoutView, MayanPasswordChangeDoneView,
    MayanPasswordChangeView, MultiFactorAuthenticationView,
    UserSetPasswordView
)
from .views.impersonation_views import (
    UserImpersonateEndView, UserImpersonateFormStartView,
    UserImpersonateStartView
)
from .views.lockout_views import UserAccountLockoutResetView
from .views.password_reset_views import (
    MayanPasswordResetCompleteView, MayanPasswordResetConfirmView,
    MayanPasswordResetDoneView, MayanPasswordResetView
)

urlpatterns_authenticattion = [
    re_path(
        route=r'^login/$', name='login_view',
        view=MayanLoginView.as_view()
    ),
    re_path(
        route=r'^login/multi_factor_authentication/$',
        name='multi_factor_authentication_view',
        view=MultiFactorAuthenticationView.as_view()
    ),
    re_path(
        route=r'^logout/$', view=MayanLogoutView.as_view(),
        name='logout_view'
    )
]

urlpatterns_lockouts = [
    re_path(
        route=r'^users/(?P<user_id>\d+)/account_lockout/reset/$',
        name='lockout_reset_single', view=UserAccountLockoutResetView.as_view()
    ),
    re_path(
        route=r'^users/multiple/account_lockout/reset/$',
        name='lockout_reset_multiple',
        view=UserAccountLockoutResetView.as_view()
    )
]

urlpatterns_password_reset = [
    re_path(
        route=r'^password/reset/complete/$',
        name='password_reset_complete_view',
        view=MayanPasswordResetCompleteView.as_view()
    ),
    path(
        'password/reset/confirm/<uidb64>/<token>/',
        name='password_reset_confirm_view',
        view=MayanPasswordResetConfirmView.as_view()
    ),
    re_path(
        route=r'^password/reset/done/$',
        name='password_reset_done_view',
        view=MayanPasswordResetDoneView.as_view()
    ),
    re_path(
        route=r'^password/reset/$', name='password_reset_view',
        view=MayanPasswordResetView.as_view()
    )
]

urlpatterns_password_set = [
    re_path(
        route=r'^password/change/done/$', name='password_change_done',
        view=MayanPasswordChangeDoneView.as_view()
    ),
    re_path(
        route=r'^password/change/$', name='password_change_view',
        view=MayanPasswordChangeView.as_view()
    ),
    re_path(
        route=r'^users/(?P<user_id>\d+)/set_password/$',
        name='user_set_password', view=UserSetPasswordView.as_view()
    ),
    re_path(
        route=r'^users/multiple/set_password/$',
        name='user_multiple_set_password',
        view=UserSetPasswordView.as_view()
    )
]

urlpatterns_user_impersonation = [
    re_path(
        route=r'^impersonate/end/$', name='user_impersonate_end',
        view=UserImpersonateEndView.as_view()
    ),
    re_path(
        route=r'^impersonate/start/$', name='user_impersonate_form_start',
        view=UserImpersonateFormStartView.as_view()
    ),
    re_path(
        route=r'^impersonate/(?P<user_id>\d+)/start/$',
        name='user_impersonate_start',
        view=UserImpersonateStartView.as_view()
    )
]

urlpatterns = []
urlpatterns.extend(urlpatterns_authenticattion)
urlpatterns.extend(urlpatterns_lockouts)
urlpatterns.extend(urlpatterns_password_reset)
urlpatterns.extend(urlpatterns_password_set)
urlpatterns.extend(urlpatterns_user_impersonation)
