from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.permissions import permission_settings_view
from mayan.apps.views.generics import SingleObjectListView

from ..classes import FileMetadataDriver
from ..icons import icon_file_metadata, icon_file_metadata_driver_list


class FileMetadataDriverListView(SingleObjectListView):
    view_icon = icon_file_metadata_driver_list
    view_permission = permission_settings_view

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_file_metadata,
            'no_results_text': _(
                message='File metadata drivers extract embedded information '
                'from document files. File metadata drivers are configure '
                'in code only.'
            ),
            'no_results_title': _(
                message='No file metadata drivers available'
            ),
            'subtitle': _(
                message='File metadata drivers enabled and detected.'
            ),
            'title': _(
                message='File metadata drivers'
            )
        }

    def get_source_queryset(self):
        return FileMetadataDriver.collection.get_all(sorted=True)
