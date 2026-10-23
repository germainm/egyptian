import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

from mayan.apps.common.validators import YAMLValidator, validate_internal_name
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave
from mayan.apps.storage.classes import DefinedStorageLazy

from .classes import Layer
from .events import event_asset_created, event_asset_edited
from .literals import STORAGE_NAME_ASSETS
from .managers import LayerTransformationManager, ObjectLayerManager
from .model_mixins import (
    AssetBusinessLogicMixin, ObjectLayerBusinessLogicMixin,
    LayerTransformationBusinessLogicMixin
)
from .transformations import BaseTransformation
from .utils import model_upload_to

logger = logging.getLogger(name=__name__)


class Asset(AssetBusinessLogicMixin, ExtraDataModelMixin, models.Model):
    _ordering_fields = ('internal_name', 'label')

    label = models.CharField(
        max_length=96, unique=True, verbose_name=_(message='Label')
    )
    internal_name = models.CharField(
        db_index=True, help_text=_(
            message='This value will be used when referencing this asset. '
            'Can only contain letters, numbers, and underscores.'
        ), max_length=255, unique=True, validators=[validate_internal_name],
        verbose_name=_(message='Internal name')
    )
    file = models.FileField(
        storage=DefinedStorageLazy(name=STORAGE_NAME_ASSETS),
        upload_to=model_upload_to, verbose_name=_(message='File')
    )
    file_hash = models.CharField(
        blank=True, editable=False, help_text=_(
            message='A hash/checksum generated from the asset file. Used to '
            'invalidate cached images that use the asset when the asset '
            'file changes.'
        ), max_length=64, null=True, verbose_name=_(message='File hash')
    )

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Asset')
        verbose_name_plural = _(message='Assets')

    def __str__(self):
        return self.label

    def delete(self, *args, **kwargs):
        self.cache_partition.delete()
        name = self.file.name
        self.file.close()
        self.file.storage.delete(name=name)
        return super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            kwargs={'asset_id': self.pk},
            viewname='converter:asset_detail'
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_asset_created,
            'target': 'self'
        },
        edited={
            'event': event_asset_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self.hash_update()
        return result


class StoredLayer(models.Model):
    name = models.CharField(
        max_length=64, unique=True, verbose_name=_(message='Name')
    )
    order = models.PositiveIntegerField(
        db_index=True, unique=True, verbose_name=_(message='Order')
    )

    class Meta:
        ordering = ('order',)
        verbose_name = _(message='Stored layer')
        verbose_name_plural = _(message='Stored layers')

    def __str__(self):
        return self.name

    def get_layer(self):
        return Layer.get(name=self.name)


class ObjectLayer(ObjectLayerBusinessLogicMixin, models.Model):
    content_type = models.ForeignKey(
        on_delete=models.CASCADE, to=ContentType,
        verbose_name=_(message='Content type')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_(message='Object ID')
    )
    content_object = GenericForeignKey(
        ct_field='content_type', fk_field='object_id'
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )
    stored_layer = models.ForeignKey(
        on_delete=models.CASCADE, related_name='object_layers',
        to=StoredLayer, verbose_name=_(message='Stored layer')
    )

    objects = ObjectLayerManager()

    class Meta:
        ordering = ('stored_layer__order',)
        unique_together = ('content_type', 'object_id', 'stored_layer')
        verbose_name = _(message='Object layer')
        verbose_name_plural = _(message='Object layers')


class LayerTransformation(
    LayerTransformationBusinessLogicMixin, models.Model
):
    object_layer = models.ForeignKey(
        on_delete=models.CASCADE, related_name='transformations',
        to=ObjectLayer, verbose_name=_(message='Object layer')
    )
    order = models.PositiveIntegerField(
        blank=True, db_index=True, default=0, help_text=_(
            message='Order in which the transformations will be executed. '
            'If left unchanged, an automatic order value will be assigned.'
        ), verbose_name=_(message='Order')
    )
    name = models.CharField(
        max_length=128, verbose_name=_(message='Name')
    )
    arguments = models.TextField(
        blank=True, help_text=_(
            message='Enter the arguments for the transformation as a YAML '
            'dictionary. ie: {"degrees": 180}'
        ), validators=[
            YAMLValidator()
        ], verbose_name=_(message='Arguments')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )

    objects = LayerTransformationManager()

    class Meta:
        ordering = ('object_layer__stored_layer__order', 'order',)
        unique_together = ('object_layer', 'order')
        verbose_name = _(message='Layer transformation')
        verbose_name_plural = _(message='Layer transformations')

    def __str__(self):
        try:
            return str(
                BaseTransformation.get(name=self.name)
            )
        except KeyError:
            return gettext(message='Unknown transformation class')

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.object_layer.get_next_order()
        super().save(*args, **kwargs)
