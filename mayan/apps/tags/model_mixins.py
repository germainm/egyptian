from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter

from .events import event_tag_attached, event_tag_removed
from .html_widgets import widget_single_tag
from .utils import get_color_contrast


class TagBusinessLogicMixin:
    @method_event(
        action_object='self',
        event=event_tag_attached,
        event_manager_class=EventManagerMethodAfter
    )
    def _attach_to(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.add(document)

    @method_event(
        action_object='self',
        event=event_tag_removed,
        event_manager_class=EventManagerMethodAfter
    )
    def _remove_from(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.remove(document)

    def attach_to(self, document, user):
        return self._attach_to(document=document, user=user)

    def get_color_contrast(self):
        return get_color_contrast(color=self.color)

    def get_document_count(self, user):
        return self.get_documents(
            permission=permission_document_view, user=user
        ).count()

    def get_documents(self, user, permission):
        queryset = Document.valid.filter(
            pk__in=self.documents.all()
        )

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission, queryset=queryset,
            user=user
        )

        return queryset

    def get_preview_widget(self):
        return widget_single_tag(tag=self)
    get_preview_widget.short_description = _(message='Preview')

    def remove_from(self, document, user):
        return self._remove_from(document=document, user=user)
