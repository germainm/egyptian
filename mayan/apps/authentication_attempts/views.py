from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SingleObjectListView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from .icons import (
    icon_user_current_login_attempt_list, icon_login_attempt_list,
    icon_user_login_attempt_list
)
from .permissions import permission_login_attempt_view


class LoginAttemptListBaseView(SingleObjectListView):
    view_icon = icon_login_attempt_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_login_attempt_list,
            'no_results_text': _(
                message='Login attempts track the successful and failed '
                'interactive authentication attempts performed against the '
                'system.'
            ),
            'no_results_title': _(message='There are no login attempts'),
            'title': _(message='Login attempts')
        }


class CurrentUserLoginAttemptListView(LoginAttemptListBaseView):
    view_icon = icon_user_current_login_attempt_list

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'object': self.request.user,
                'no_results_text': _(
                    message='Your successful and failed login attempts will '
                    'appear here.'
                ),
                'title': _(message='My login attempts')
            }
        )
        return context

    def get_source_queryset(self):
        return self.request.user.login_attempts.all()


class LoginAttemptListView(LoginAttemptListBaseView):
    object_permission = permission_login_attempt_view
    view_icon = icon_login_attempt_list

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'title': _(message='Login attempts (all users)')
            }
        )
        return context

    def get_source_queryset(self):
        LoginAttempt = apps.get_model(
            app_label='authentication_attempts', model_name='LoginAttempt'
        )
        return LoginAttempt.objects.all()


class UserLoginAttemptListView(
    ExternalObjectViewMixin, LoginAttemptListBaseView
):
    external_object_class = get_user_model()
    external_object_pk_url_kwarg = 'user_id'
    external_object_permission = permission_login_attempt_view
    view_icon = icon_user_login_attempt_list

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'object': self.external_object,
                'title': _(
                    message='Login attempts of user: %s'
                ) % self.external_object
            }
        )
        return context

    def get_source_queryset(self):
        return self.external_object.login_attempts.all()
