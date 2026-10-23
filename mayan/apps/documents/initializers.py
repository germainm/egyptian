from django.apps import apps

from .literals import DEFAULT_DOCUMENT_TYPE_LABEL
from .signals import signal_post_initial_document_type


def initializer_create_default_document_type():
    DocumentType = apps.get_model(
        app_label='documents', model_name='DocumentType'
    )

    if not DocumentType.objects.count():
        document_type = DocumentType.objects.create(
            label=DEFAULT_DOCUMENT_TYPE_LABEL
        )
        signal_post_initial_document_type.send(
            sender=DocumentType, instance=document_type
        )
