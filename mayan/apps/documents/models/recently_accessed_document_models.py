from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..managers import (
    RecentlyAccessedDocumentManager, ValidRecentlyAccessedDocumentManager
)

from .document_models import Document

__all__ = ('RecentlyAccessedDocument',)


class RecentlyAccessedDocument(models.Model):
    user = models.ForeignKey(
        db_index=True, editable=False, on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL, verbose_name=_(message='User')
    )
    document = models.ForeignKey(
        editable=False, on_delete=models.CASCADE, related_name='recent',
        to=Document, verbose_name=_(message='Document')
    )
    datetime_accessed = models.DateTimeField(
        auto_now=True, db_index=True, verbose_name=_(message='Accessed')
    )

    objects = RecentlyAccessedDocumentManager()
    valid = ValidRecentlyAccessedDocumentManager()

    class Meta:
        ordering = ('-datetime_accessed',)
        verbose_name = _(message='Recent document')
        verbose_name_plural = _(message='Recent documents')

    def __str__(self):
        return str(self.document)

    def natural_key(self):
        return (
            self.datetime_accessed, self.document.natural_key(),
            self.user.natural_key()
        )
    natural_key.dependencies = [
        'documents.Document', settings.AUTH_USER_MODEL
    ]


class RecentlyAccessedDocumentProxy(Document):
    class Meta:
        proxy = True
        verbose_name = _(message='Recently accessed document')
        verbose_name_plural = _(message='Recently accessed documents')
