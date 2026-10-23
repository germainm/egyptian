from django.apps import apps
from django.utils.translation import gettext_lazy as _

from .classes import DuplicateBackend


class DuplicateBackendFileChecksum(DuplicateBackend):
    label = _(message='Exact document file checksum')

    @classmethod
    def verify(cls, document):
        return document.file_latest

    def process(self, document):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )


        return Document.valid.filter(
            file_latest__checksum=document.file_latest.checksum
        ).exclude(pk=document.pk)


class DuplicateBackendLabel(DuplicateBackend):
    label = _(message='Exact document label')

    def process(self, document):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        return Document.objects.filter(
            label=document.label
        ).exclude(pk=document.pk)
