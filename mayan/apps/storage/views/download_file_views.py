from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    MultipleObjectDeleteView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ViewMixinOwnerPlusFilteredQueryset

from ..events import event_download_file_downloaded
from ..icons import (
    icon_download_file_delete, icon_download_file_download,
    icon_download_file_list
)
from ..models import DownloadFile
from ..permissions import (
    permission_download_file_delete, permission_download_file_download,
    permission_download_file_view
)

from .download_views import ViewSingleObjectDownload


class DownloadFileDeleteView(
    ViewMixinOwnerPlusFilteredQueryset, MultipleObjectDeleteView
):
    model = DownloadFile
    object_optional_permission = permission_download_file_delete
    pk_url_kwarg = 'download_file_id'
    post_action_redirect = reverse_lazy(
        viewname='storage:download_file_list'
    )
    view_icon = icon_download_file_delete

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class DownloadFileDownloadView(
    ViewMixinOwnerPlusFilteredQueryset, ViewSingleObjectDownload
):
    download_event_type = event_download_file_downloaded
    model = DownloadFile
    object_optional_permission = permission_download_file_download
    pk_url_kwarg = 'download_file_id'
    view_icon = icon_download_file_download

    def get_download_file_object(self):
        instance = self.get_object()
        instance._event_actor = self.request.user
        return instance.open(mode='rb')

    def get_download_filename(self):
        return self.object.filename or str(self.object)


class DownloadFileListView(
    ViewMixinOwnerPlusFilteredQueryset, SingleObjectListView
):
    model = DownloadFile
    object_optional_permission = permission_download_file_view
    view_icon = icon_download_file_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_download_file_list,
            'no_results_text': _(
                'Download files are created as a results of a an external '
                'process like an export. Download files are retained over '
                'a span of time and then removed automatically.'
            ),
            'no_results_title': _(message='There are no files to download'),
            'title': _(message='Downloads')
        }
