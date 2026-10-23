import logging

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

from .classes import CredentialBackend
from .forms import (
    StoredCredentialBackendDynamicForm, StoredCredentialBackendSelectionForm
)
from .icons import (
    icon_credential_backend_selection, icon_credential_create,
    icon_credential_delete, icon_credential_edit, icon_credential_list,
    icon_credentials
)
from .links import link_credential_backend_selection
from .models import StoredCredential
from .permissions import (
    permission_credential_create, permission_credential_delete,
    permission_credential_edit, permission_credential_view
)

logger = logging.getLogger(name=__name__)


class StoredCredentialBackendSelectionView(FormView):
    extra_context = {
        'submit_label': _(message='Next'),
        'title': _(message='New credential backend selection')
    }
    form_class = StoredCredentialBackendSelectionForm
    view_icon = icon_credential_backend_selection
    view_permission = permission_credential_create

    def form_valid(self, form):
        backend = form.cleaned_data['backend']
        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={'backend_path': backend},
                viewname='credentials:stored_credential_create'
            )
        )


class StoredCredentialCreateView(ViewSingleObjectDynamicFormModelBackendCreate):
    backend_class = CredentialBackend
    form_class = StoredCredentialBackendDynamicForm
    post_action_redirect = reverse_lazy(
        viewname='credentials:stored_credential_list'
    )
    view_icon = icon_credential_create
    view_permission = permission_credential_create

    def get_extra_context(self):
        backend_class = self.get_backend_class()

        return {
            'title': _(
                message='Create a "%s" credential'
            ) % backend_class.label
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'backend_path': self.kwargs['backend_path']
        }


class StoredCredentialDeleteView(SingleObjectDeleteView):
    model = StoredCredential
    object_permission = permission_credential_delete
    pk_url_kwarg = 'stored_credential_id'
    post_action_redirect = reverse_lazy(
        viewname='credentials:stored_credential_list'
    )
    view_icon = icon_credential_delete

    def get_extra_context(self):
        return {
            'title': _(message='Delete credential: %s') % self.object
        }


class StoredCredentialEditView(ViewSingleObjectDynamicFormModelBackendEdit):
    form_class = StoredCredentialBackendDynamicForm
    model = StoredCredential
    object_permission = permission_credential_edit
    pk_url_kwarg = 'stored_credential_id'
    view_icon = icon_credential_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit credential: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class StoredCredentialListView(SingleObjectListView):
    model = StoredCredential
    object_permission = permission_credential_view
    view_icon = icon_credential_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_credentials,
            'no_results_main_link': link_credential_backend_selection.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Credentials represent an identity. '
                'These are used to when accessing external systems or '
                'services.'
            ),
            'no_results_title': _(message='No credentials available'),
            'title': _(message='Credentials')
        }
