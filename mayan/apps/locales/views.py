from django.contrib.auth.decorators import login_not_required
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.i18n import JavaScriptCatalog

from mayan.apps.user_management.permissions import (
    permission_user_edit, permission_user_view
)
from mayan.apps.user_management.querysets import get_user_queryset
from mayan.apps.user_management.views.view_mixins import (
    DynamicExternalUserViewMixin
)
from mayan.apps.views.generics import (
    SingleObjectDetailView, SingleObjectEditView
)
from mayan.apps.views.view_mixins import (
    ExternalObjectViewMixin, RedirectWithPageReloadViewMixin
)

from .forms import LocaleProfileForm, LocaleProfileForm_view
from .icons import (
    icon_user_locale_profile_detail, icon_user_locale_profile_edit
)


@method_decorator(login_not_required, name='dispatch')
class JavaScriptCatalogPublic(JavaScriptCatalog):
    pass


class UserLocaleProfileDetailView(
    DynamicExternalUserViewMixin, ExternalObjectViewMixin,
    SingleObjectDetailView
):
    form_class = LocaleProfileForm_view
    external_object_permission = permission_user_view
    external_object_pk_url_kwarg = 'user_id'
    view_icon = icon_user_locale_profile_detail

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self, **kwargs):
        return {
            'form': LocaleProfileForm_view(
                instance=self.external_object.locale_profile
            ),
            'object': self.external_object,
            'read_only': True,
            'title': _(
                message='Locale profile for user: %s'
            ) % self.external_object
        }

    def get_object(self):
        return self.external_object.locale_profile


class UserLocaleProfileEditView(
    DynamicExternalUserViewMixin, ExternalObjectViewMixin,
    RedirectWithPageReloadViewMixin, SingleObjectEditView
):
    form_class = LocaleProfileForm
    external_object_permission = permission_user_edit
    external_object_pk_url_kwarg = 'user_id'
    view_icon = icon_user_locale_profile_edit

    def form_valid(self, form):
        if self.is_current_user:
            language_value = form.cleaned_data['language']
            timezone_value = form.cleaned_data['timezone']

            timezone.activate(timezone=timezone_value)
            translation.activate(language=language_value)

        return super().form_valid(form=form)

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='Edit locale profile for user: %s'
            ) % self.external_object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_object(self):
        return self.external_object.locale_profile

    def get_page_reload_enabled(self):
        return self.is_current_user
