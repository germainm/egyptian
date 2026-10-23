from django.apps import apps

from .events import event_ocr_document_version_submitted
from .tasks import task_document_version_ocr_process


def method_document_ocr_content(self):
    version_active = self.version_active

    if version_active:
        return version_active.ocr_content()
    else:
        return ()


def method_document_ocr_submit(self, user=None):
    version_active = self.version_active
    if version_active:
        version_active.submit_for_ocr(user=user)


def method_document_version_ocr_content(self):
    DocumentVersionPageOCRContent = apps.get_model(
        app_label='ocr', model_name='DocumentVersionPageOCRContent'
    )

    queryset = self.pages.select_related('ocr_content')

    for page in queryset:
        try:
            page_content = page.ocr_content.content
        except DocumentVersionPageOCRContent.DoesNotExist:
            """Not critical, just ignore and go to next page."""
        else:
            yield page_content


def method_document_version_ocr_submit(self, user=None):
    if user:
        user_id = user.pk
    else:
        user_id = None

    event_ocr_document_version_submitted.commit(
        action_object=self.document, actor=user, target=self
    )

    task_document_version_ocr_process.apply_async(
        kwargs={
            'document_version_id': self.pk, 'user_id': user_id
        }
    )
