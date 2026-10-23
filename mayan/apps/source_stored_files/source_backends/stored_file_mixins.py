import logging

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import APIException

from mayan.apps.converter.classes import AppImageErrorImage
from mayan.apps.converter.exceptions import AppImageError
from mayan.apps.converter.utils import factory_file_generator

from ..classes import SourceStoredFile
from ..forms import StoredFileUploadForm
from ..source_backend_actions.stored_file_actions import (
    SourceBackendActionFileStoredDeleteInteractive,
    SourceBackendActionFileStoredDeleteInteractiveNot,
    SourceBackendActionFileStoredDocumentFileUpload,
    SourceBackendActionFileStoredDocumentUpload,
    SourceBackendActionFileStoredImage, SourceBackendActionFileStoredList
)
from ..views import SourceBackendStoredFileSourceFileListView

from .literals import DEFAULT_PREVIEW_WIDTH

logger = logging.getLogger(name=__name__)


class SourceBackendMixinStoredFileUploadBase:
    upload_form_class = StoredFileUploadForm

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'delete_after_upload': {
                    'class': 'django.forms.BooleanField',
                    'help_text': _(
                        message='Delete the file after is has been '
                        'successfully uploaded.'
                    ),
                    'label': _(message='Delete after upload'),
                    'required': False
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='File content'), {
                    'fields': ('delete_after_upload',)
                },
            ),
        )

        return fieldsets

    def get_view_context(self, context, request):
        try:
            source_stored_file_list = list(
                self.get_stored_file_list()
            )
        except Exception as exception:
            messages.error(
                message=_(
                    message='Unable get list of files; %s'
                ) % exception, request=request
            )
            source_stored_file_list = ()
            if settings.DEBUG or settings.TESTING:
                raise

        view = SourceBackendStoredFileSourceFileListView()
        view.kwargs = self.kwargs
        view.object_list = source_stored_file_list
        view.request = request

        template_source_stored_file_list_context = {
            'hide_link': True,
            'no_results_icon': self.icon,
            'no_results_text': _(
                message='This could mean that the source file list is empty. '
                'It could also mean that the operating system user account '
                'being used for Mayan EDMS doesn\'t have the necessary file '
                'system permissions to access the source files.'
            ),
            'no_results_title': _(message='No source files available')
        }

        template_source_stored_file_list_context.update(
            view.get_context_data()
        )

        subtemplates_list = [
            {
                'context': {
                    'forms': context['forms']
                },
                'name': 'appearance/partials/form/multiple.html'
            },
            {
                'context': template_source_stored_file_list_context,
                'name': 'appearance/partials/list/table.html'
            }
        ]

        return {'subtemplates_list': subtemplates_list}


class SourceBackendMixinStoredFileDocumentFileUpload(
    SourceBackendMixinStoredFileUploadBase
):
    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (
            SourceBackendActionFileStoredDocumentFileUpload,
        )

        return action_class_list


class SourceBackendMixinStoredFileDocumentUpload(
    SourceBackendMixinStoredFileUploadBase
):
    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (SourceBackendActionFileStoredDocumentUpload,)

        return action_class_list


class SourceBackendMixinStoredFileDeleteInteractive:
    def action_file_delete(self, encoded_filename):
        source_stored_file = self.get_stored_file(
            encoded_filename=encoded_filename
        )

        source_stored_file.delete()

    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (
            SourceBackendActionFileStoredDeleteInteractive,
        )

        return action_class_list


class SourceBackendMixinStoredFileDeleteInteractiveNot:
    def action_file_delete(self, encoded_filename):
        source_stored_file = self.get_stored_file(
            encoded_filename=encoded_filename
        )

        source_stored_file.delete()

    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (
            SourceBackendActionFileStoredDeleteInteractiveNot,
        )

        return action_class_list


class SourceBackendMixinStoredFileImage:
    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'preview_width': {
                    'class': 'django.forms.IntegerField',
                    'default': DEFAULT_PREVIEW_WIDTH,
                    'help_text': _(
                        message='Width value to be passed to the converter '
                        'backend.'
                    ),
                    'kwargs': {
                        'min_value': 0
                    },
                    'label': _(message='Preview width'),
                    'required': True
                },
                'preview_height': {
                    'class': 'django.forms.IntegerField',
                    'help_text': _(
                        message='Height value to be passed to the image '
                        'converter backend. Leave blank to have the image '
                        'converter calculate the correct aspect ratio for '
                        'the specified preview width.'
                    ),
                    'kwargs': {
                        'min_value': 0
                    },
                    'label': _(message='Preview height'),
                    'required': False
                },
                'preview_max_size': {
                    'class': 'django.forms.IntegerField',
                    'default': SourceStoredFile.DEFAULT_PREVIEW_MAX_SIZE,
                    'help_text': _(
                        message='Maximum file size in bytes for which '
                        'previews will be generated. Example: 20000 = 20KB.'
                    ),
                    'label': _(message='Max size preview'),
                    'required': True
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='File images'), {
                    'fields': (
                        'preview_width', 'preview_height',
                        'preview_max_size'
                    )
                },
            ),
        )

        return fieldsets

    def action_file_image(
        self, encoded_filename, maximum_layer_order=None,
        transformation_instance_list=None, user=None
    ):
        if maximum_layer_order:
            maximum_layer_order = int(maximum_layer_order)

        source_stored_file = self.get_stored_file(
            encoded_filename=encoded_filename
        )

        combined_transformation_list = source_stored_file.get_combined_transformation_list(
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )

        try:
            cache_filename = source_stored_file.generate_image(
                transformation_instance_list=combined_transformation_list
            )
        except AppImageError as exception:
            app_image_error_image = AppImageErrorImage.get(
                name=exception.error_name
            )

            error_image_template_result = app_image_error_image.render()

            detail = {
                'app_image_error_image_template': error_image_template_result
            }

            raise APIException(detail=detail)
        else:
            cache_partition_file = source_stored_file.cache_partition.get_file(
                filename=cache_filename
            )
            return factory_file_generator(image_object=cache_partition_file)

    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (SourceBackendActionFileStoredImage,)

        return action_class_list


class SourceBackendMixinStoredFileList:
    def action_file_list(self):
        for source_stored_file in self.get_stored_file_list():
            yield {
                'encoded_filename': source_stored_file.encoded_filename,
                'filename': source_stored_file.filename,
                'size': source_stored_file.get_size()
            }

    def get_action_class_list(self):
        action_class_list = super().get_action_class_list()

        action_class_list += (SourceBackendActionFileStoredList,)

        return action_class_list
