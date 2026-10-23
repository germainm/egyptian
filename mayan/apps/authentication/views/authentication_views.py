from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, login as django_auth_login
)
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeDoneView, PasswordChangeView,
    RedirectURLMixin
)
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.urls import reverse, reverse_lazy
from django.utils.decorators import classonlymethod, method_decorator
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from formtools.wizard.views import SessionWizardView, StepsHelper

from mayan.apps.common.settings import setting_home_view
from mayan.apps.forms import formsets
from mayan.apps.user_management.permissions import permission_user_edit
from mayan.apps.user_management.querysets import (
    get_all_users_queryset, get_user_queryset
)
from mayan.apps.views.generics import MultipleObjectFormActionView
from mayan.apps.views.http import URL
from mayan.apps.views.view_mixins import ViewIconMixin

from ..classes import AuthenticationBackend
from ..forms import AuthenticationFormBase
from ..icons import icon_login, icon_password_change
from ..literals import (
    SESSION_MULTI_FACTOR_USER_BACKEND_KEY, SESSION_MULTI_FACTOR_USER_ID_KEY
)


class MultiFactorAuthenticationView(RedirectURLMixin, SessionWizardView):
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = 'authentication/login.html'

    get_default_redirect_url = LoginView.get_default_redirect_url
    get_redirect_url = LoginView.get_redirect_url
    get_success_url = LoginView.get_success_url

    @staticmethod
    def condition_dict(self):
        self.authentication_backend = AuthenticationBackend.cls_get_instance()
        condition_dict = self.authentication_backend.get_condition_dict()
        return condition_dict

    @staticmethod
    def form_list_property(self):
        self.authentication_backend = AuthenticationBackend.cls_get_instance()
        form_list = self.authentication_backend.get_form_list()
        computed_form_list = OrderedDict()

        for form_index, form in enumerate(iterable=form_list):
            computed_form_list[
                str(form_index)
            ] = form

        for form in computed_form_list.values():
            if issubclass(form, formsets.BaseFormSet):
                form = form.form

        return computed_form_list

    @classonlymethod
    def as_view(cls, *args, **kwargs):
        class EmptyForm(AuthenticationFormBase):
            pass

        cls.form_list = [EmptyForm]

        result = super().as_view(*args, **kwargs)

        def null_setter(self, value):
            return

        cls.form_list = property(
            fget=MultiFactorAuthenticationView.form_list_property,
            fset=null_setter
        )
        cls.condition_dict = property(
            fget=MultiFactorAuthenticationView.condition_dict,
            fset=null_setter
        )

        return result

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(login_not_required)
    def dispatch(self, request, *args, **kwargs):
        steps = StepsHelper(self)

        if steps.count == 0:
            user_id = request.session.get(
                SESSION_MULTI_FACTOR_USER_ID_KEY, None
            )
            if user_id:
                return self.done()
            else:
                redirect_to = resolve_url(to=settings.LOGIN_URL)
                return HttpResponseRedirect(redirect_to=redirect_to)
        else:
            return super().dispatch(request=request, *args, **kwargs)

    def done(self, form_list=None, **kwargs):
        kwargs = self.get_all_cleaned_data()
        self.authentication_backend.do_process(
            form_list=form_list, kwargs=kwargs, request=self.request
        )
        user = self.authentication_backend.get_user(
            form_list=form_list, kwargs=kwargs, request=self.request
        )

        backend = self.request.session.pop(
            SESSION_MULTI_FACTOR_USER_BACKEND_KEY, None
        )
        self.request.session.pop(SESSION_MULTI_FACTOR_USER_ID_KEY, None)

        if not backend:
            raise ValueError(
                'Multi-factor login cannot complete: the first-factor '
                'authentication backend was not recorded in the session.'
            )

        django_auth_login(backend=backend, request=self.request, user=user)

        redirect_to = self.get_success_url()
        return HttpResponseRedirect(redirect_to=redirect_to)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        authentication_backend = AuthenticationBackend.cls_get_instance()
        authentication_backend_context = authentication_backend.get_context_data()
        context.update(authentication_backend_context)

        wizard_step = self.form_list[self.steps.current]

        if self.storage.current_step == self.steps.last:
            context['submit_label'] = None
        else:
            context['submit_label'] = _(message='Next')

        context.update(
            {
                'form_css_classes': 'form-hotkey-double-click',
                'step_title': _(
                    message='Step %(step)d of %(total_steps)d: '
                    '%(step_label)s'
                ) % {
                    'step': self.steps.step1,
                    'step_label': wizard_step._label,
                    'total_steps': len(self.form_list)
                },
                'wizard_step': wizard_step,
                'wizard_steps': self.form_list
            }
        )
        return context

    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['wizard'] = self
        return kwargs


@method_decorator(login_not_required, name='dispatch')
class MayanLoginView(LoginView):
    extra_context = {
        'appearance_type': 'plain',
        'submit_icon': icon_login,
        'submit_label': _(message='Sign in')
    }
    redirect_authenticated_user = True
    template_name = 'authentication/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        authentication_backend = AuthenticationBackend.cls_get_instance()
        authentication_backend_context = authentication_backend.get_context_data()
        context.update(authentication_backend_context)

        return context

    def get_form_class(self):
        authentication_backend = AuthenticationBackend.cls_get_instance()
        return authentication_backend.get_login_form_class()

    def form_valid(self, form):
        if not AuthenticationBackend.cls_get_instance().form_list:
            authentication_backend = AuthenticationBackend.cls_get_instance()
            authentication_backend.do_process(
                kwargs=form.cleaned_data, request=self.request

            )
            return super().form_valid(form=form)
        else:
            user = form.get_user()

            self.request.session[
                SESSION_MULTI_FACTOR_USER_BACKEND_KEY
            ] = user.backend

            self.request.session[
                SESSION_MULTI_FACTOR_USER_ID_KEY
            ] = form.get_user().pk

            url = URL(
                path=reverse(
                    viewname='authentication:multi_factor_authentication_view'
                )
            )

            next_url = self.get_redirect_url()
            if next_url:
                url.args[self.redirect_field_name] = next_url

            return HttpResponseRedirect(
                redirect_to=url.to_string()
            )


class MayanLogoutView(LogoutView):
    pass


class MayanPasswordChangeDoneView(PasswordChangeDoneView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(
            message=_(
                message='Your password has been successfully changed.'
            ),
            request=request
        )
        return redirect(
            to=request.user.get_absolute_url()
        )


class MayanPasswordChangeView(ViewIconMixin, PasswordChangeView):
    extra_context = {
        'submit_label': _(message='Change password'),
        'title': _(message='Current user password change')
    }
    success_url = reverse_lazy(
        viewname='authentication:password_change_done'
    )
    template_name = 'appearance/form_container.html'
    view_icon = icon_password_change

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.user_options.block_password_change:
            messages.error(
                message=_(
                    message='Changing the password is not allowed for '
                    'this account.'
                ), request=self.request
            )
            return HttpResponseRedirect(
                redirect_to=reverse(viewname=setting_home_view.view)
            )

        return super().dispatch(request=request, *args, **kwargs)


class UserSetPasswordView(MultipleObjectFormActionView):
    form_class = SetPasswordForm
    object_permission = permission_user_edit
    pk_url_kwarg = 'user_id'
    source_queryset = get_user_queryset()
    success_message = _(
        message='Password change request performed on %(count)d user'
    )
    success_message_plural = _(
        message='Password change request performed on %(count)d users'
    )
    view_icon = icon_password_change

    def dispatch(self, request, *args, **kwargs):
        queryset_requested = self.get_queryset_requested()

        queryset_allowed = self.get_queryset()
        pk_list_allowed = queryset_allowed.values('pk')

        queryset_excluded = queryset_requested.exclude(
            pk__in=pk_list_allowed
        )

        if queryset_excluded.exists():
            list_username = list(
                queryset_excluded.values_list('username', flat=True)
            )
            text_username = ', '.join(list_username)

            messages.warning(
                message=ngettext(
                    singular='The password of the account %(usernames)s '
                    'was not changed. Changing the password of staff or '
                    'super user accounts via the user interface is not '
                    'allowed. Use administration tools to perform this '
                    'operation.',
                    plural='The password of the accounts %(usernames)s '
                    'was not changed. Changing the password of staff or '
                    'super user accounts via the user interface is not '
                    'allowed. Use administration tools to perform this '
                    'operation.',
                    number=queryset_excluded.count()
                ) % {'usernames': text_username}, request=request
            )

            queryset_included = queryset_requested.filter(
                pk__in=pk_list_allowed
            )

            if not queryset_included.exists():
                return HttpResponseRedirect(
                    redirect_to=self.get_previous_url()
                )

        return super().dispatch(request=request, *args, **kwargs)

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'title': ngettext(
                singular='Change user password',
                plural='Change users passwords',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Change password for user: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_form_extra_kwargs(self):
        queryset = self.object_list
        result = {}
        if queryset:
            result['user'] = queryset.first()
            return result
        else:
            raise PermissionDenied

    def get_pk_list_requested(self):
        result = []

        pk = self.kwargs.get(self.pk_url_kwarg)

        if pk is not None:
            result.append(pk)

        pk_list = self.get_pk_list()

        if pk_list is not None:
            result.extend(pk_list)

        return result

    def get_queryset_requested(self):
        pk_list_requested = self.get_pk_list_requested()

        queryset_all_users = self.get_queryset(
            source_queryset=get_all_users_queryset()
        )

        return queryset_all_users.filter(pk__in=pk_list_requested)

    def object_action(self, form, instance):
        try:
            instance.set_password(
                raw_password=form.cleaned_data['new_password1']
            )
            instance.save()
            messages.success(
                message=_(
                    message='Successful password reset for user: %s.'
                ) % instance, request=self.request
            )
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error resetting password for user '
                    '"%(user)s": %(error)s'
                ) % {
                    'error': exception, 'user': instance
                }, request=self.request
            )
