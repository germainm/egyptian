from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import TaskDeduplicationEntryManager


class TaskDeduplicationEntry(models.Model):
    dotted_path = models.CharField(
        db_index=True, help_text=_(
            message='Python path of the task type the marker suppresses.'
        ), max_length=255, verbose_name=_(message='Dotted path')
    )
    key = models.TextField(
        help_text=_(
            message='Serialized keyword arguments identifying the unit of '
            'work requested.'
        ), verbose_name=_(message='Key')
    )
    key_hash = models.CharField(
        help_text=_(
            message='Hash of the key. The unique constraint is applied to '
            'this field and not to the key itself because the length of a '
            'key is decided by the task requesting the work, and an index '
            'over an unbounded column exceeds the size limit of some '
            'database managers.'
        ), max_length=64, verbose_name=_(message='Key hash')
    )
    datetime_created = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text=_(
            message='Date and time the work was requested or last '
            're-dispatched. A marker whose work has not begun stops '
            'suppressing requests once this is older than the queued '
            'interval, which is what allows a worker that ended before '
            'publishing its task to recover without intervention.'
        ), verbose_name=_(message='Created')
    )
    datetime_started = models.DateTimeField(
        blank=True, db_index=True, null=True, help_text=_(
            message='Date and time a worker began performing the work. '
            'Until it is set, the task the marker stands for is still '
            'waiting in the queue and has not read the object it will '
            'act on, so a request arriving in that period asks for work '
            'the queued task is already going to perform.'
        ), verbose_name=_(message='Started')
    )
    is_dirty = models.BooleanField(
        default=False, help_text=_(
            message='A new request for the same unit of work arrived after '
            'the task began performing it, therefore too late for the task '
            'to take it into account. The work is dispatched once more when '
            'the task completes.'
        ), verbose_name=_(message='Is dirty?')
    )

    objects = TaskDeduplicationEntryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('dotted_path', 'key_hash'),
                name='task_manager_taskdeduplicationentry_unique_key'
            )
        ]
        ordering = ('datetime_created',)
        verbose_name = _(message='Task deduplication entry')
        verbose_name_plural = _(message='Task deduplication entries')

    def __str__(self):
        return '{}: {}'.format(self.dotted_path, self.key)
