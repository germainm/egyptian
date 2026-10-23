from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_(message='Documents'), name='documents'
)


event_document_created = namespace.add_event_type(
    label=_(message='Document created'), name='document_create'
)
event_document_edited = namespace.add_event_type(
    label=_(message='Document edited'), name='document_edit'
)
event_document_viewed = namespace.add_event_type(
    label=_(message='Document viewed'), name='document_view'
)


event_document_file_created = namespace.add_event_type(
    label=_(message='Document file created'), name='document_file_created'
)
event_document_file_deleted = namespace.add_event_type(
    label=_(message='Document file deleted'), name='document_file_deleted'
)
event_document_file_edited = namespace.add_event_type(
    label=_(message='Document file edited'), name='document_file_edited'
)


event_document_type_created = namespace.add_event_type(
    label=_(message='Document type created'), name='document_type_created'
)
event_document_type_edited = namespace.add_event_type(
    label=_(message='Document type edited'), name='document_type_edit'
)
event_document_type_quick_label_created = namespace.add_event_type(
    label=_(message='Document type quick label created'),
    name='document_type_quick_label_created'
)
event_document_type_quick_label_deleted = namespace.add_event_type(
    label=_(message='Document type quick label deleted'),
    name='document_type_quick_label_deleted'
)
event_document_type_quick_label_edited = namespace.add_event_type(
    label=_(message='Document type quick label edited'),
    name='document_type_quick_label_edited'
)
event_document_type_changed = namespace.add_event_type(
    label=_(message='Document type changed'), name='document_type_change'
)


event_document_version_created = namespace.add_event_type(
    label=_(message='Document version created'), name='document_version_created'
)
event_document_version_deleted = namespace.add_event_type(
    label=_(message='Document version deleted'), name='document_version_deleted'
)
event_document_version_edited = namespace.add_event_type(
    label=_(message='Document version edited'), name='document_version_edited'
)


event_document_version_page_created = namespace.add_event_type(
    label=_(message='Document version page created'),
    name='document_version_page_created'
)
event_document_version_page_deleted = namespace.add_event_type(
    label=_(message='Document version page deleted'),
    name='document_version_page_deleted'
)
event_document_version_page_edited = namespace.add_event_type(
    label=_(message='Document version page edited'),
    name='document_version_page_edited'
)


event_document_trashed = namespace.add_event_type(
    label=_(message='Document trashed'), name='document_trashed'
)
event_trashed_document_deleted = namespace.add_event_type(
    label=_(message='Trashed document deleted'), name='trashed_document_deleted'
)
event_trashed_document_restored = namespace.add_event_type(
    label=_(message='Trashed document restored'), name='trashed_document_restored'
)


event_document_download = namespace.add_event_type(
    label=_(message='Document downloaded (historic)'), name='document_download'
)
event_document_file_pre_save = namespace.add_event_type(
    label=_(message='Document file created (historic)'),
    name='document_file_pre_save'
)
event_document_version_revert = namespace.add_event_type(
    label=_(message='Document version reverted (historic)'),
    name='document_version_revert'
)
event_document_version_new = namespace.add_event_type(
    label=_(message='Document version uploaded (historic)'),
    name='document_new_version'
)
