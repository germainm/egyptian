from django.apps import apps
from django.core.exceptions import PermissionDenied

from mayan.apps.navigation.column_widgets import SourceColumnWidget

from .permissions import permission_tag_view


class DocumentTagWidget(SourceColumnWidget):
    template_name = 'tags/document_tags_widget.html'

    def get_extra_context(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        try:
            AccessControlList.objects.check_access(
                obj=self.value, permission=permission_tag_view,
                user=self.request.user
            )
        except PermissionDenied:
            queryset = self.value.tags.none()
        else:
            queryset = self.value.get_tags(
                permission=permission_tag_view, user=self.request.user
            )

        return {'tags': queryset}
