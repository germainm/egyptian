from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.user_management.permissions import permission_user_edit
from mayan.apps.user_management.querysets import get_user_queryset
from mayan.apps.views.generics import FormView
from mayan.apps.views.view_mixins import (
    ExternalObjectViewMixin, RedirectWithPageReloadViewMixin
)

from .classes import Theme
from .forms import ThemeForm
from .icons import icon_theme
from .literals import (
    COOKIE_MAX_AGE, COOKIE_NAME_THEME, USER_THEME_SETTING_KEY,
    USER_THEME_SETTING_NAMESPACE
)
from .models import UserSetting


class CurrentUserThemeEditView(RedirectWithPageReloadViewMixin, FormView):
    form_class = ThemeForm
    success_url = reverse_lazy(viewname='appearance:user_current_theme_edit')
    view_icon = icon_theme

    def form_valid(self, form):
        value = form.cleaned_data['theme']

        UserSetting.objects.do_value_set(
            key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=self.request.user,
            value=value
        )

        messages.success(
            message=_(message='Your theme preference has been updated.'),
            request=self.request
        )

        response = super().form_valid(form=form)
        response.set_cookie(
            key=COOKIE_NAME_THEME, max_age=COOKIE_MAX_AGE, samesite='Lax',
            value=value
        )
        return response

    def get_extra_context(self):
        return {
            'object': self.request.user,
            'submit_label': _(message='Save'),
            'title': _(message='Theme')
        }

    def get_initial(self):
        theme = Theme.get_for_request(request=self.request)

        return {
            'theme': getattr(theme, 'name', None)
        }


class UserThemeEditView(ExternalObjectViewMixin, FormView):
    external_object_permission = permission_user_edit
    external_object_pk_url_kwarg = 'user_id'
    form_class = ThemeForm
    view_icon = icon_theme

    def form_valid(self, form):
        UserSetting.objects.do_value_set(
            key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=self.external_object,
            value=form.cleaned_data['theme']
        )

        messages.success(
            message=_(
                message='Theme updated for user: %s'
            ) % self.external_object, request=self.request
        )

        return super().form_valid(form=form)

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'submit_label': _(message='Save'),
            'title': _(
                message='Edit theme for user: %s'
            ) % self.external_object
        }

    def get_initial(self):
        name = UserSetting.objects.do_value_get(
            key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=self.external_object
        )
        theme = Theme.get(name=name) or Theme.get_default()

        return {
            'theme': getattr(theme, 'name', None)
        }

    def get_success_url(self):
        return reverse(
            kwargs={'user_id': self.external_object.pk},
            viewname='appearance:user_theme_edit'
        )
