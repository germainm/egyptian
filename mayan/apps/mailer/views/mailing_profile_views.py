from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.views import (
    ViewSingleObjectDynamicFormModelBackendCreate,
    ViewSingleObjectDynamicFormModelBackendEdit
)
from mayan.apps.views.generics import (
    FormView, SingleObjectDeleteView, SingleObjectListView
)
from mayan.apps.views.view_mixins import (
    ExternalObjectViewMixin, ViewMixinFormSaveAndTest
)

from ..classes import MailerBackend
from ..forms import (
    UserMailerBackendSelectionForm, UserMailerSetupDynamicForm,
    UserMailerTestForm
)
from ..icons import (
    icon_mailing_profile_backend_select, icon_mailing_profile_create,
    icon_mailing_profile_delete, icon_mailing_profile_edit,
    icon_mailing_profile_list, icon_mailing_profile_test
)
from ..links import link_mailing_profile_create
from ..models import UserMailer
from ..permissions import (
    permission_mailing_profile_create, permission_mailing_profile_delete,
    permission_mailing_profile_edit, permission_mailing_profile_use,
    permission_mailing_profile_view
)


class MailingProfileBackendSelectionView(FormView):
    extra_context = {
        'submit_label': _(message='Next'),
        'title': _(message='New mailing profile backend selection')
    }
    form_class = UserMailerBackendSelectionForm
    view_icon = icon_mailing_profile_backend_select
    view_permission = permission_mailing_profile_create

    def form_valid(self, form):
        backend = form.cleaned_data['backend']
        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={
                    'backend_path': backend
                }, viewname='mailer:mailing_profile_create'
            )
        )


class MailingProfileCreateView(ViewSingleObjectDynamicFormModelBackendCreate):
    backend_class = MailerBackend
    form_class = UserMailerSetupDynamicForm
    post_action_redirect = reverse_lazy(
        viewname='mailer:mailing_profile_list'
    )
    view_icon = icon_mailing_profile_create
    view_permission = permission_mailing_profile_create

    def get_extra_context(self):
        backend_class = self.get_backend_class()

        return {
            'title': _(
                message='Create a "%s" mailing profile'
            ) % backend_class.label
        }

    def get_form_extra_kwargs(self):
        return {'user': self.request.user}

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'backend_path': self.kwargs['backend_path']
        }


class MailingProfileDeleteView(SingleObjectDeleteView):
    model = UserMailer
    object_permission = permission_mailing_profile_delete
    pk_url_kwarg = 'mailing_profile_id'
    post_action_redirect = reverse_lazy(
        viewname='mailer:mailing_profile_list'
    )
    view_icon = icon_mailing_profile_delete

    def get_extra_context(self):
        return {
            'title': _(message='Delete mailing profile: %s') % self.object
        }


class MailingProfileEditView(
    ViewMixinFormSaveAndTest, ViewSingleObjectDynamicFormModelBackendEdit
):
    form_class = UserMailerSetupDynamicForm
    form_save_and_test_label = _(message='Send test')
    model = UserMailer
    object_permission = permission_mailing_profile_edit
    pk_url_kwarg = 'mailing_profile_id'
    view_icon = icon_mailing_profile_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit mailing profile: %s') % self.object
        }

    def get_form_extra_kwargs(self):
        return {'user': self.request.user}

    def get_form_save_and_test_available(self):
        return bool(self.request.user.email)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def view_test(self):
        recipient = self.request.user.email
        self.object.test(to=recipient, user=self.request.user)

        messages.success(
            message=_(message='Test email sent.'), request=self.request
        )


class MailingProfileListView(SingleObjectListView):
    model = UserMailer
    object_permission = permission_mailing_profile_view
    view_icon = icon_mailing_profile_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_mailing_profile_list,
            'no_results_main_link': link_mailing_profile_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Mailing profiles are email configurations. '
                'Mailing profiles allow sending documents as '
                'attachments or as links via email.'
            ),
            'no_results_title': _(message='No mailing profiles available'),
            'title': _(message='Mailing profiles')
        }

    def get_form_schema(self):
        backend_class = self.get_backend_class()
        return {'fields': backend_class.fields}


class MailingProfileTestView(ExternalObjectViewMixin, FormView):
    external_object_class = UserMailer
    external_object_permission = permission_mailing_profile_use
    external_object_pk_url_kwarg = 'mailing_profile_id'
    form_class = UserMailerTestForm
    view_icon = icon_mailing_profile_test

    def form_valid(self, form):
        self.external_object.test(
            to=form.cleaned_data['email'], user=self.request.user
        )
        messages.success(
            message=_(message='Test email sent.'), request=self.request
        )
        return super().form_valid(form=form)

    def get_extra_context(self):
        return {
            'hide_object': True,
            'object': self.external_object,
            'submit_label': _(message='Test'),
            'title': _(
                message='Test mailing profile: %s'
            ) % self.external_object
        }
