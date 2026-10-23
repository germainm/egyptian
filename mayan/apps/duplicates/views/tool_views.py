from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_tools
from mayan.apps.views.generics import ConfirmView

from ..icons import icon_duplicated_document_scan
from ..tasks import task_duplicates_scan_all


class ScanDuplicatedDocuments(ConfirmView):
    extra_context = {
        'submit_label': _(message='Scan'),
        'title': _(message='Scan for duplicated documents?')
    }
    view_permission = permission_document_tools
    view_icon = icon_duplicated_document_scan

    def view_action(self):
        task_duplicates_scan_all.apply_async()
        messages.success(
            message=_(message='Duplicated document scan queued successfully.'),
            request=self.request
        )
