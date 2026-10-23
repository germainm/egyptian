import logging

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.serialization import yaml_load
from .classes import Layer
from .transformations import BaseTransformation

logger = logging.getLogger(name=__name__)


class LayerTransformationManager(models.Manager):
    def get_for_object(
        self, obj, as_classes=False, maximum_layer_order=None,
        only_stored_layer=None, user=None
    ):
        Layer.update()

        StoredLayer = apps.get_model(
            app_label='converter', model_name='StoredLayer'
        )
        content_type = ContentType.objects.get_for_model(model=obj)

        transformations = self.filter(
            enabled=True, object_layer__content_type=content_type,
            object_layer__enabled=True, object_layer__object_id=obj.pk
        )

        if only_stored_layer:
            transformations = transformations.filter(
                object_layer__stored_layer=only_stored_layer
            )

        if not transformations:
            if as_classes:
                return []
            else:
                return transformations

        layer_access_filtering_required = (
            maximum_layer_order is not None
        ) or any(
            layer.permission_map.get('access') for layer in Layer.all()
        )

        if layer_access_filtering_required:
            if maximum_layer_order is not None:
                access_layers = StoredLayer.objects.filter(
                    order__lte=maximum_layer_order
                )
                exclude_layers = StoredLayer.objects.filter(
                    order__gt=maximum_layer_order
                )
            else:
                access_layers = StoredLayer.objects.all()
                exclude_layers = StoredLayer.objects.none()

            for stored_layer in access_layers:
                try:
                    layer_class = stored_layer.get_layer()
                except KeyError:
                    """
                    This was a class defined but later erased. Ignore it.
                    """
                else:
                    access_permission = layer_class.permission_map.get(
                        'access', None
                    )
                    if access_permission:
                        try:
                            AccessControlList.objects.check_access(
                                obj=obj, permission=access_permission,
                                user=user
                            )
                        except PermissionDenied:
                            access_layers = access_layers.exclude(
                                pk=stored_layer.pk
                            )

            for stored_layer in exclude_layers:
                layer = stored_layer.get_layer()
                exclude_permission = layer.permission_map.get(
                    'exclude', None
                )
                if exclude_permission:
                    try:
                        AccessControlList.objects.check_access(
                            obj=obj, permission=exclude_permission, user=user
                        )
                    except PermissionDenied:
                        exclude_layers = exclude_layers.exclude(
                            pk=stored_layer.pk
                        )
                        access_layers |= StoredLayer.objects.filter(
                            pk=stored_layer.pk
                        )

            transformations = transformations.filter(
                object_layer__stored_layer__in=access_layers
            )

            transformations = transformations.exclude(
                object_layer__stored_layer__in=exclude_layers
            )

        if as_classes:
            result = []
            for transformation in transformations:
                try:
                    transformation_class = BaseTransformation.get(
                        transformation.name
                    )
                except KeyError:
                    logger.error(
                        'Non existent transformation: %s for %s',
                        transformation.name, obj
                    )
                else:
                    try:
                        if transformation.arguments:
                            kwargs = yaml_load(
                                stream=transformation.arguments
                            )
                        else:
                            kwargs = {}

                        tranformation_instance = transformation_class(
                            **kwargs
                        )
                        tranformation_instance.object_layer = transformation.object_layer
                        result.append(
                            tranformation_instance
                        )
                    except Exception as exception:
                        logger.error(
                            'Error while parsing transformation "%s", '
                            'arguments "%s", for object "%s"; %s',
                            transformation, transformation.arguments, obj,
                            exception, exc_info=True
                        )

            return result
        else:
            return transformations

    def get_for_object_list(
        self, object_list, as_classes=False, maximum_layer_order=None,
        only_stored_layer=None, user=None
    ):
        object_list = list(object_list)

        result = {}

        for obj in object_list:
            if as_classes:
                result[obj.pk] = []
            else:
                result[obj.pk] = self.none()

        if not object_list:
            return result

        Layer.update()

        content_type_map = {}

        for obj in object_list:
            content_type = ContentType.objects.get_for_model(model=obj)
            content_type_map.setdefault(
                content_type, []
            ).append(obj)

        object_id_set = set()

        for content_type, content_type_object_list in content_type_map.items():
            queryset = self.filter(
                enabled=True, object_layer__content_type=content_type,
                object_layer__enabled=True,
                object_layer__object_id__in=[
                    obj.pk for obj in content_type_object_list
                ]
            )

            if only_stored_layer:
                queryset = queryset.filter(
                    object_layer__stored_layer=only_stored_layer
                )

            object_id_set.update(
                queryset.values_list('object_layer__object_id', flat=True)
            )

        for obj in object_list:
            if obj.pk in object_id_set:
                result[obj.pk] = self.get_for_object(
                    as_classes=as_classes,
                    maximum_layer_order=maximum_layer_order, obj=obj,
                    only_stored_layer=only_stored_layer, user=user
                )

        return result


class ObjectLayerManager(models.Manager):
    def get_for(self, layer, obj):
        content_type = ContentType.objects.get_for_model(model=obj)

        return self.get_or_create(
            content_type=content_type, object_id=obj.pk,
            stored_layer=layer.stored_layer
        )
