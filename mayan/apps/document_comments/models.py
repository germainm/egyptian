from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from .events import (
    event_document_comment_created, event_document_comment_deleted,
    event_document_comment_edited
)
from .model_mixins import CommentBusinessLogicMixin


class Comment(CommentBusinessLogicMixin, ExtraDataModelMixin, models.Model):
    _event_created_event = event_document_comment_created
    _event_edited_event = event_document_comment_created
    _ordering_fields = ('submit_date',)

    document = models.ForeignKey(
        db_index=True, on_delete=models.CASCADE, related_name='comments',
        to=Document, verbose_name=_(message='Document')
    )
    user = models.ForeignKey(
        editable=False,
        help_text=_(message='The user account that made the comment.'),
        on_delete=models.CASCADE, related_name='comments',
        to=settings.AUTH_USER_MODEL, verbose_name=_(message='User')
    )
    text = models.TextField(
        help_text=_(message='Actual text content of the comment.'),
        verbose_name=_(message='Text')
    )
    submit_date = models.DateTimeField(
        auto_now_add=True, db_index=True,
        verbose_name=_(message='Date time submitted')
    )

    class Meta:
        get_latest_by = 'submit_date'
        ordering = ('-submit_date',)
        verbose_name = _(message='Comment')
        verbose_name_plural = _(message='Comments')

    def __str__(self):
        return self.text

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_document_comment_deleted,
        target='document'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            viewname='comments:comment_details', kwargs={
                'comment_id': self.pk
            }
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'actor': 'user',
            'action_object': 'document',
            'event': event_document_comment_created,
            'target': 'self'
        },
        edited={
            'action_object': 'document',
            'event': event_document_comment_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
