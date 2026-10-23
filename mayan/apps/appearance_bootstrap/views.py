from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.appearance.models import UserSetting
from mayan.apps.user_management.permissions import permission_user_edit
from mayan.apps.user_management.querysets import get_user_queryset
from mayan.apps.views.generics import FormView
from mayan.apps.views.view_mixins import (
    ExternalObjectViewMixin, RedirectWithPageReloadViewMixin
)

from .classes import ColorMode
from .forms import ColorModeForm
from .icons import icon_color_mode
from .literals import (
    COOKIE_MAX_AGE, COOKIE_NAME_COLOR_MODE, USER_COLOR_MODE_SETTING_KEY,
    USER_COLOR_MODE_SETTING_NAMESPACE
)


class CurrentUserColorModeEditView(RedirectWithPageReloadViewMixin, FormView):
    form_class = ColorModeForm
    success_url = reverse_lazy(
        viewname='appearance_bootstrap:user_current_color_mode_edit'
    )
    view_icon = icon_color_mode

    def form_valid(self, form):
        value = form.cleaned_data['color_mode']

        UserSetting.objects.do_value_set(
            key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE,
            user=self.request.user, value=value
        )

        messages.success(
            message=_(message='Your color mode preference has been updated.'),
            request=self.request
        )

        response = super().form_valid(form=form)
        response.set_cookie(
            key=COOKIE_NAME_COLOR_MODE, max_age=COOKIE_MAX_AGE,
            samesite='Lax', value=value
        )
        return response

    def get_extra_context(self):
        return {
            'object': self.request.user,
            'submit_label': _(message='Save'),
            'title': _(message='Color mode')
        }

    def get_initial(self):
        color_mode = ColorMode.get_for_request(request=self.request)

        return {
            'color_mode': getattr(color_mode, 'name', None)
        }


class UserColorModeEditView(ExternalObjectViewMixin, FormView):
    external_object_permission = permission_user_edit
    external_object_pk_url_kwarg = 'user_id'
    form_class = ColorModeForm
    view_icon = icon_color_mode

    def form_valid(self, form):
        UserSetting.objects.do_value_set(
            key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE,
            user=self.external_object, value=form.cleaned_data['color_mode']
        )

        messages.success(
            message=_(
                message='Color mode updated for user: %s'
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
                message='Edit color mode for user: %s'
            ) % self.external_object
        }

    def get_initial(self):
        name = UserSetting.objects.do_value_get(
            key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE,
            user=self.external_object
        )
        color_mode = ColorMode.get(name=name) or ColorMode.get_default()

        return {
            'color_mode': getattr(color_mode, 'name', None)
        }

    def get_success_url(self):
        return reverse(
            kwargs={'user_id': self.external_object.pk},
            viewname='appearance_bootstrap:user_color_mode_edit'
        )
