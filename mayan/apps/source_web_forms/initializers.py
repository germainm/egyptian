from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.source_compressed.source_backends.literals import (
    SOURCE_UNCOMPRESS_CHOICE_ASK
)

from .source_backends import SourceBackendWebForm


def initializer_create_default_document_source():
    Source = apps.get_model(
        app_label='sources', model_name='Source'
    )

    queryset_source_web_forms = Source.objects.filter(
        backend_path=SourceBackendWebForm.get_class_path()
    )

    if not queryset_source_web_forms.exists():
        Source.objects.create_backend(
            backend_path=SourceBackendWebForm.get_class_path(),
            backend_data={
                'uncompress': SOURCE_UNCOMPRESS_CHOICE_ASK
            }, label=_(message='Default')
        )
