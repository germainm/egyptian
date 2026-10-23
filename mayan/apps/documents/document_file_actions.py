from django.apps import apps
from django.utils.translation import gettext_lazy as _

from .classes import DocumentFileAction


class DocumentFileActionAppendNewPages(DocumentFileAction):
    action_id = 'append'
    label = _(
        message='Append. Create a new version and append the new file pages.'
    )

    @staticmethod
    def execute(document, document_file, comment, user):
        DocumentVersion = apps.get_model(
            app_label='documents', model_name='DocumentVersion'
        )

        annotated_content_object_list = []

        version_active = document.version_active

        if version_active:
            content_object_list = version_active.page_content_objects
            annotated_content_object_list_original = DocumentVersion.annotate_content_object_list(
                content_object_list=content_object_list
            )
            annotated_content_object_list.extend(
                annotated_content_object_list_original
            )

            start_page_number = version_active.pages.count() + 1
        else:
            start_page_number = 1

        content_object_list = document_file.pages.all()
        annotated_content_object_list_new = DocumentVersion.annotate_content_object_list(
            content_object_list=content_object_list,
            start_page_number=start_page_number
        )
        annotated_content_object_list.extend(
            annotated_content_object_list_new
        )

        document_version = DocumentVersion(
            active=True, comment=comment, document=document
        )
        document_version.pages_remap(
            annotated_content_object_list=annotated_content_object_list,
            user=user
        )


class DocumentFileActionNothing(DocumentFileAction):
    action_id = 'keep'
    label = _(
        message='Keep. Do not create a new version and keep the current '
        'version pages.'
    )

    @staticmethod
    def execute(document, document_file, comment, user):
        return


class DocumentFileActionUseNewPages(DocumentFileAction):
    action_id = 'replace'
    label = _(message='Replace. Create a new version and use the new file pages.')

    @staticmethod
    def execute(document, document_file, comment, user):
        DocumentVersion = apps.get_model(
            app_label='documents', model_name='DocumentVersion'
        )

        content_object_list = document_file.pages.all()
        annotated_content_object_list = DocumentVersion.annotate_content_object_list(
            content_object_list=content_object_list
        )

        document_version = DocumentVersion(
            active=True, comment=comment, document=document
        )
        document_version.pages_remap(
            annotated_content_object_list=annotated_content_object_list,
            user=user
        )
