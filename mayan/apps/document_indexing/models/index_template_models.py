from django.db import models
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)
from mayan.apps.events.models import StoredEventType

from ..events import event_index_template_created, event_index_template_edited
from ..managers import IndexTemplateManager

from .index_template_model_mixins import (
    IndexTemplateBusinessLogicMixin, IndexTemplateNodeBusinessLogicMixin
)


class IndexTemplate(
    ExtraDataModelMixin, IndexTemplateBusinessLogicMixin, models.Model
):
    _ordering_fields = ('enabled', 'label', 'slug')

    label = models.CharField(
        help_text=_(message='Short description of this index.'),
        max_length=128, unique=True, verbose_name=_(message='Label')
    )
    slug = models.SlugField(
        help_text=_(
            message='This value will be used by other apps to reference this '
            'index.'
        ), max_length=128, unique=True, verbose_name=_(message='Slug')
    )
    enabled = models.BooleanField(
        default=True, help_text=_(
            message='Causes this index to be visible and updated when '
            'document data changes.'
        ), verbose_name=_(message='Enabled')
    )
    document_types = models.ManyToManyField(
        related_name='index_templates', to=DocumentType,
        verbose_name=_(message='Document types')
    )

    objects = IndexTemplateManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Index template')
        verbose_name_plural = _(message='Index templates')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(
            kwargs={'index_template_id': self.pk},
            viewname='indexing:index_template_view'
        )

    def natural_key(self):
        return (self.slug,)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_index_template_created,
            'target': 'self',
        },
        edited={
            'event': event_index_template_edited,
            'target': 'self',
        }
    )
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            IndexTemplateNode.objects.get_or_create(parent=None, index=self)
            self.do_event_triggers_populate()

        self.index_template_root_node.initialize_index_instance_root_node()


class IndexTemplateEventTrigger(ExtraDataModelMixin, models.Model):
    index_template = models.ForeignKey(
        on_delete=models.CASCADE, related_name='event_triggers',
        to=IndexTemplate, verbose_name=_(message='Index template')
    )
    stored_event_type = models.ForeignKey(
        on_delete=models.CASCADE, to=StoredEventType,
        verbose_name=_(message='Event type')
    )

    class Meta:
        unique_together = ('index_template', 'stored_event_type')
        verbose_name = _(message='Index template event trigger')
        verbose_name_plural = _(message='Index template event triggers')

    def __str__(self):
        return str(self.stored_event_type)

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_index_template_edited,
        target='index_template'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_index_template_edited,
            'target': 'index_template'
        },
        edited={
            'event': event_index_template_edited,
            'target': 'index_template'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class IndexTemplateNode(IndexTemplateNodeBusinessLogicMixin, MPTTModel):
    _ordering_fields = ('enabled', 'link_documents')

    parent = TreeForeignKey(
        blank=True, help_text=_(
            message='Parent index template node of this node.'
        ), null=True, on_delete=models.CASCADE, related_name='children',
        to='self'
    )
    index = models.ForeignKey(
        on_delete=models.CASCADE, related_name='index_template_nodes',
        to=IndexTemplate, verbose_name=_(message='Index')
    )
    expression = models.TextField(
        help_text=_(
            message='Enter a template to render. Use Django\'s default '
            'templating language.'
        ),
        verbose_name=_(message='Indexing expression')
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_(
            message='Causes this node to be visible and updated when '
            'document data changes.'
        ),
        verbose_name=_(message='Enabled')
    )
    link_documents = models.BooleanField(
        default=False,
        help_text=_(
            message='Check this option to have this node act as a container '
            'for documents and not as a parent for further nodes.'
        ),
        verbose_name=_(message='Link documents')
    )

    class Meta:
        verbose_name = _(message='Index template node')
        verbose_name_plural = _(message='Index template nodes')

    def __str__(self):
        if self.is_root_node():
            return gettext(message='Root')
        else:
            return self.expression
