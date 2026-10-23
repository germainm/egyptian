from django.apps import apps
from django.utils.html import conditional_escape

from .events import event_parsing_document_file_submitted
from .tasks import task_parse_document_file


def method_document_content(self):
    file_latest = self.file_latest
    if file_latest:
        return file_latest.content()
    else:
        return []


def method_document_parsing_submit(self, user=None):
    latest_file = self.file_latest
    if latest_file:
        latest_file.submit_for_parsing(user=user)


def method_document_file_content(document_file):
    DocumentFilePageContent = apps.get_model(
        app_label='document_parsing', model_name='DocumentFilePageContent'
    )

    for page in document_file.pages.all():
        try:
            page_content = page.content.content
        except DocumentFilePageContent.DoesNotExist:
            """Page has no content, skip."""
        else:
            yield conditional_escape(
                text=str(page_content)
            )


def method_document_file_parsing_submit(self, user=None):
    if user:
        user_id = user.pk
    else:
        user_id = None

    event_parsing_document_file_submitted.commit(
        action_object=self.document, actor=user, target=self
    )

    task_parse_document_file.apply_async(
        kwargs={'document_file_pk': self.pk, 'user_id': user_id}
    )
