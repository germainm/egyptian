import logging

from django.contrib import messages
from django.template import RequestContext
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter
from mayan.apps.storage.views.download_views import ViewSingleObjectDownload
from mayan.apps.views.generics import (
    ConfirmView, SingleObjectCreateView, SingleObjectDeleteView,
    SingleObjectDetailView, SingleObjectListView, SimpleView
)

from .events import event_key_downloaded
from .forms import KeyDetailForm, KeySearchForm
from .icons import (
    icon_key_delete, icon_key_detail, icon_key_download, icon_key_setup,
    icon_key_upload, icon_keyserver_search, icon_private_key_list,
    icon_public_key_list
)
from .links import link_key_query, link_key_upload
from .literals import KEY_TYPE_PUBLIC
from .models import Key
from .permissions import (
    permission_key_delete, permission_key_download, permission_key_receive,
    permission_key_upload, permission_key_view, permission_keyserver_query
)

logger = logging.getLogger(name=__name__)


class KeyDeleteView(SingleObjectDeleteView):
    model = Key
    object_permission = permission_key_delete
    pk_url_kwarg = 'key_id'
    view_icon = icon_key_delete

    def get_extra_context(self):
        return {
            'title': _(message='Delete key: %s') % self.object
        }

    def get_post_action_redirect(self):
        if self.object.key_type == KEY_TYPE_PUBLIC:
            return reverse_lazy(viewname='django_gpg:key_public_list')
        else:
            return reverse_lazy(viewname='django_gpg:key_private_list')


class KeyDetailView(SingleObjectDetailView):
    form_class = KeyDetailForm
    model = Key
    object_permission = permission_key_view
    pk_url_kwarg = 'key_id'
    view_icon = icon_key_detail

    def get_extra_context(self):
        return {
            'title': _(message='Details for key: %s') % self.object
        }


class KeyDownloadView(ViewSingleObjectDownload):
    model = Key
    object_permission = permission_key_download
    pk_url_kwarg = 'key_id'
    view_icon = icon_key_download

    @method_event(
        actor='request.user',
        event_manager_class=EventManagerMethodAfter,
        event=event_key_downloaded,
        target='object'
    )
    def get_download_file_object(self):
        return super().get_download_file_object()

    def get_download_filename(self):
        return self.object.key_id


class KeyReceive(ConfirmView):
    post_action_redirect = reverse_lazy(
        viewname='django_gpg:key_public_list'
    )
    view_icon = icon_key_upload
    view_permission = permission_key_receive

    def get_extra_context(self):
        return {
            'message': _(message='Import key ID: %s?') % self.kwargs['key_id'],
            'title': _(message='Import key')
        }

    def view_action(self):
        try:
            Key.objects.receive_key(
                key_id=self.kwargs['key_id']
            )
        except Exception as exception:
            messages.error(
                message=_(
                    message='Unable to import key: %(key_id)s; %(error)s'
                ) % {
                    'key_id': self.kwargs['key_id'],
                    'error': exception,
                }, request=self.request
            )
        else:
            messages.success(
                message=_(message='Successfully received key: %(key_id)s') % {
                    'key_id': self.kwargs['key_id'],
                }, request=self.request
            )


class KeyQueryResultView(SingleObjectListView):
    view_icon = icon_keyserver_search
    view_permission = permission_keyserver_query

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_key_setup,
            'no_results_main_link': link_key_query.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Use names, last names, key ids or emails to search '
                'public keys to import from the keyserver.'
            ),
            'no_results_title': _(
                message='No results returned'
            ),
            'title': _(message='Key query results')
        }

    def get_source_queryset(self):
        term = self.request.GET.get('term')
        if term:
            return Key.objects.search(query=term)
        else:
            return ()


class KeyQueryView(SimpleView):
    template_name = 'appearance/form_container.html'
    view_icon = icon_keyserver_search
    view_permission = permission_keyserver_query

    def get_extra_context(self):
        return {
            'form': self.get_form(),
            'form_action': reverse(viewname='django_gpg:key_query_results'),
            'submit_label': _(message='Search'),
            'submit_method': 'GET',
            'title': _(message='Query key server')
        }

    def get_form(self):
        if ('term' in self.request.GET) and self.request.GET['term'].strip():
            term = self.request.GET['term']
            return KeySearchForm(
                initial={'term': term}
            )
        else:
            return KeySearchForm()


class KeyUploadView(SingleObjectCreateView):
    fields = ('key_data',)
    model = Key
    post_action_redirect = reverse_lazy(
        viewname='django_gpg:key_public_list'
    )
    view_icon = icon_key_upload
    view_permission = permission_key_upload

    def get_extra_context(self):
        return {
            'title': _(message='Upload new key')
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class PrivateKeyListView(SingleObjectListView):
    object_permission = permission_key_view
    source_queryset = Key.objects.private_keys()
    view_icon = icon_private_key_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_private_key_list,
            'no_results_main_link': link_key_upload.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Private keys are used to sign documents. '
                'Private keys can only be uploaded by the user. '
                'The view to upload private and public keys is the same.'
            ),
            'no_results_title': _(
                message='There are no private keys'
            ),
            'title': _(message='Private keys')
        }


class PublicKeyListView(SingleObjectListView):
    object_permission = permission_key_view
    source_queryset = Key.objects.public_keys()
    view_icon = icon_public_key_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_public_key_list,
            'no_results_main_link': link_key_upload.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Public keys are used to verify signed documents. '
                'Public keys can be uploaded by the user or downloaded '
                'from keyservers. The view to upload private and public '
                'keys is the same.'
            ),
            'no_results_title': _(
                message='There are no public keys'
            ),
            'title': _(message='Public keys')
        }
