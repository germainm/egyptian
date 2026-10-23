from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from mayan.apps.documents.models.document_models import Document

from ..managers import DocumentIndexInstanceNodeManager, IndexInstanceManager

from .index_instance_model_mixins import (
    IndexInstanceBusinessLogicMixin, IndexInstanceNodeBusinessLogicMixin
)
from .index_template_models import IndexTemplate, IndexTemplateNode


class IndexInstance(IndexInstanceBusinessLogicMixin, IndexTemplate):
    objects = IndexInstanceManager()

    class Meta:
        proxy = True
        verbose_name = _(message='Index instance')
        verbose_name_plural = _(message='Index instances')

    def get_absolute_url(self):
        try:
            index_instance_root_node = self.index_instance_root_node
        except IndexInstanceNode.DoesNotExist:
            return '#'
        else:
            return reverse(
                kwargs={
                    'index_instance_node_id': index_instance_root_node.pk
                }, viewname='indexing:index_instance_node_view'
            )


class IndexInstanceNode(IndexInstanceNodeBusinessLogicMixin, MPTTModel):
    _ordering_fields = ('value',)

    parent = TreeForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        related_name='children', to='self'
    )
    index_template_node = models.ForeignKey(
        on_delete=models.CASCADE, related_name='index_instance_nodes',
        to=IndexTemplateNode, verbose_name=_(message='Index template node')
    )
    value = models.CharField(
        blank=True, db_index=True, max_length=255,
        verbose_name=_(message='Value')
    )
    documents = models.ManyToManyField(
        related_name='index_instance_nodes', to=Document,
        verbose_name=_(message='Documents')
    )

    class Meta:
        ordering = ('value',)
        unique_together = ('index_template_node', 'parent', 'value')
        verbose_name = _(message='Index instance node')
        verbose_name_plural = _(message='Indexes instances node')

    def __str__(self):
        return self.value

    def get_absolute_url(self):
        return reverse(
            kwargs={'index_instance_node_id': self.pk},
            viewname='indexing:index_instance_node_view'
        )


class DocumentIndexInstanceNode(IndexInstanceNode):
    objects = DocumentIndexInstanceNodeManager()

    class Meta:
        proxy = True
        verbose_name = _(message='Document index node instance')
        verbose_name_plural = _(message='Document indexes node instances')


class IndexInstanceNodeSearchResult(IndexInstanceNode):
    class Meta:
        proxy = True
        verbose_name = _(message='Index instance node')
        verbose_name_plural = _(message='Index instance nodes')
