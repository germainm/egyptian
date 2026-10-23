from django.template import RequestContext
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.views.generics import (
    MultipleObjectConfirmActionView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_document_file_metadata_driver_list,
    icon_document_file_metadata_submit_multiple, icon_file_metadata,
    icon_file_metadata_driver_attribute_list
)
from ..links import link_document_file_metadata_submit_single
from ..models import DocumentFileDriverEntry
from ..permissions import (
    permission_file_metadata_submit, permission_file_metadata_view
)


class DocumentFileMetadataDriverListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_file_metadata_view
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_metadata_driver_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_file_metadata,
            'no_results_main_link': link_document_file_metadata_submit_single.resolve(
                context=RequestContext(
                    dict_={
                        'resolved_object': self.external_object
                    }, request=self.request
                )
            ),
            'no_results_text': _(
                message='File metadata are the attributes of the document\'s '
                'file. They can range from camera information used to take a '
                'photo to the author that created a file. File metadata are '
                'set when the document\'s file was first created. File '
                'metadata attributes reside in the file itself. They are not '
                'the same as the document metadata, which are user defined '
                'and reside in the database.'
            ),
            'no_results_title': _(message='No file metadata available'),
            'object': self.external_object,
            'title': _(
                message='File metadata drivers for: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        queryset_driver_entries = self.external_object.file_metadata_drivers.select_related(
            'driver'
        )

        return queryset_driver_entries


class DocumentFileMetadataDriverAttributeListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_file_metadata_view
    external_object_pk_url_kwarg = 'document_file_driver_id'
    view_icon = icon_file_metadata_driver_attribute_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_file_metadata,
            'no_results_main_link': link_document_file_metadata_submit_single.resolve(
                context=RequestContext(
                    dict_={
                        'resolved_object': self.external_object.document_file
                    }, request=self.request
                )
            ),
            'no_results_text': _(
                message='This could mean that the file metadata detection '
                'has not completed or that the driver does not support '
                'any metadata field for the file type of this document.'
            ),
            'no_results_title': _(
                message='No file metadata available for this driver'
            ),
            'object': self.external_object.document_file,
            'title': _(
                message='File metadata attributes for: %(document_file)s '
                'with driver: %(driver)s'
            ) % {
                'document_file': self.external_object.document_file,
                'driver': self.external_object.driver
            }
        }

    def get_external_object_queryset(self):
        queryset_document_files = DocumentFile.valid.all()
        return DocumentFileDriverEntry.objects.filter(
            document_file_id__in=queryset_document_files.values('pk')
        )

    def get_source_queryset(self):
        queryset_entries = self.external_object.entries.select_related(
            'document_file_driver_entry__driver'
        )

        return queryset_entries


class DocumentFileMetadataSubmitView(MultipleObjectConfirmActionView):
    object_permission = permission_file_metadata_submit
    pk_url_kwarg = 'document_file_id'
    source_queryset = DocumentFile.valid.all()
    success_message_plural = _(
        message='%(count)d documents files submitted to the file metadata '
        'queue.'
    )
    success_message_singular = _(
        message='%(count)d document file submitted to the file metadata '
        'queue.'
    )
    view_icon = icon_document_file_metadata_submit_multiple

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'submit_label': _(message='Submit'),
            'title': ngettext(
                singular='Submit the selected document file to the file metadata queue?',
                plural='Submit the selected documents files to the file metadata queue?',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result['object'] = queryset.first()

        return result

    def object_action(self, form, instance):
        instance.submit_for_file_metadata_processing(user=self.request.user)
