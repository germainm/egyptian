from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import (
    PasswordResetCompleteView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetView
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

import mayan
from mayan.apps.common.settings import setting_home_view
from mayan.apps.organizations.utils import get_organization_installation_url

from ..settings import setting_disable_password_reset


class MayanPasswordResetRedirectMixin:
    def get(self, *args, **kwargs):
        if setting_disable_password_reset.value:
            return redirect(to=setting_home_view.value)
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if setting_disable_password_reset.value:
            return redirect(to=setting_home_view.value)
        return super().post(*args, **kwargs)


@method_decorator(login_not_required, name='dispatch')
class MayanPasswordResetCompleteView(
    MayanPasswordResetRedirectMixin, PasswordResetCompleteView
):
    extra_context = {
        'appearance_type': 'plain'
    }
    template_name = 'authentication/password_reset_complete.html'


@method_decorator(login_not_required, name='dispatch')
class MayanPasswordResetConfirmView(
    MayanPasswordResetRedirectMixin, PasswordResetConfirmView
):
    extra_context = {
        'appearance_type': 'plain'
    }
    success_url = reverse_lazy(
        viewname='authentication:password_reset_complete_view'
    )
    template_name = 'authentication/password_reset_confirm.html'


@method_decorator(login_not_required, name='dispatch')
class MayanPasswordResetDoneView(
    MayanPasswordResetRedirectMixin, PasswordResetDoneView
):
    extra_context = {
        'appearance_type': 'plain'
    }
    template_name = 'authentication/password_reset_done.html'


@method_decorator(login_not_required, name='dispatch')
class MayanPasswordResetView(
    MayanPasswordResetRedirectMixin, PasswordResetView
):
    email_template_name = 'authentication/password_reset_email.html'
    extra_context = {
        'appearance_type': 'plain'
    }
    subject_template_name = 'authentication/password_reset_subject.txt'
    success_url = reverse_lazy(
        viewname='authentication:password_reset_done_view'
    )
    template_name = 'authentication/password_reset_form.html'

    def form_valid(self, form):
        opts = {
            'email_template_name': self.email_template_name,
            'extra_email_context': self.get_extra_email_context(),
            'from_email': self.from_email,
            'html_email_template_name': self.html_email_template_name,
            'request': self.request,
            'subject_template_name': self.subject_template_name,
            'token_generator': self.token_generator,
            'use_https': self.request.is_secure()
        }
        form.save(**opts)
        return super(PasswordResetView, self).form_valid(form=form)

    def get_extra_email_context(self):
        extra_email_context_project_website = get_organization_installation_url(
            request=self.request
        )
        extra_email_context = {
            'project_copyright': mayan.__copyright__,
            'project_license': mayan.__license__,
            'project_title': mayan.__title__,
            'project_website': str(extra_email_context_project_website)
        }
        return extra_email_context
