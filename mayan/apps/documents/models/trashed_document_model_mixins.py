from django.apps import apps

from mayan.apps.converter.exceptions import AppImageError
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter

from ..events import event_trashed_document_restored
from ..literals import IMAGE_ERROR_DOCUMENT_VERSION_HAS_NO_PAGES


class TrashedDocumentBusinessLogicMixin:
    @property
    def document(self):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        return Document.objects.get(pk=self.pk)

    def get_api_image_url(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        first_page = self.pages.first()
        if first_page:
            return first_page.get_api_image_url(
                maximum_layer_order=None, transformation_instance_list=None,
                view_kwargs={'document_id': self.pk},
                viewname='rest_api:trasheddocument-image', user=user
            )
        else:
            raise AppImageError(
                error_name=IMAGE_ERROR_DOCUMENT_VERSION_HAS_NO_PAGES
            )

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_trashed_document_restored, target='document'
    )
    def restore(self, user):
        self._event_actor = user
        self.in_trash = False
        self.trashed_date_time = None
        self._event_ignore = True
        self.save(
            update_fields=('in_trash', 'trashed_date_time')
        )
