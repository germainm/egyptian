from functools import partial

from django.db import transaction

from mayan.apps.common.compatibility import Iterable
from mayan.apps.common.utils import (
    ResolverPipelineModelAttribute, flatten_list
)

from .tasks import (
    task_deindex_instance, task_index_instance,
    task_index_related_instance_m2m
)


def handler_deindex_instance(sender, **kwargs):
    instance = kwargs['instance']

    # Queue the task only once the deletion is committed. Queued earlier,
    # it could run first and an index task that still sees the instance
    # would add it back to the index.
    transaction.on_commit(
        func=partial(
            task_deindex_instance.apply_async, kwargs={
                'app_label': instance._meta.app_label,
                'model_name': instance._meta.model_name,
                'object_id': instance.pk
            }
        ), using=kwargs.get('using')
    )


def handler_factory_index_related_instance_delete(reverse_field_path):
    def handler_index_by_related_to_delete_instance(sender, **kwargs):
        related_instance = kwargs['instance']

        result = ResolverPipelineModelAttribute.resolve(
            attribute=reverse_field_path, obj=related_instance
        )

        def call_task(instance):
            # Same as handler_deindex_instance: wait for the deletion to be
            # committed so an instance deleted along with the related one is
            # not indexed again.
            transaction.on_commit(
                func=partial(
                    task_index_instance.apply_async, kwargs={
                        'app_label': instance._meta.app_label,
                        'exclude_app_label': related_instance._meta.app_label,
                        'exclude_kwargs': {'id': related_instance.pk},
                        'exclude_model_name': related_instance._meta.model_name,
                        'model_name': instance._meta.model_name,
                        'object_id': instance.pk
                    }
                ), using=kwargs.get('using')
            )

        is_iterable = isinstance(result, Iterable)
        is_single = isinstance(
            result, (str, bytes)
        )

        if is_iterable and not is_single:
            for instance in flatten_list(value=result):
                call_task(instance=instance)
        else:
            call_task(instance=result)

    return handler_index_by_related_to_delete_instance


def handler_factory_index_related_instance_save(
    reverse_field_path, field_name_set=None
):
    def handler_index_by_related_instance(sender, **kwargs):
        related_instance = kwargs['instance']

        update_fields = kwargs.get('update_fields')

        if field_name_set is not None and update_fields is not None:
            if field_name_set.isdisjoint(update_fields):
                return

        result = ResolverPipelineModelAttribute.resolve(
            attribute=reverse_field_path, obj=related_instance
        )

        def call_task(instance):
            task_index_instance.apply_async(
                kwargs={
                    'app_label': instance._meta.app_label,
                    'model_name': instance._meta.model_name,
                    'object_id': instance.pk
                }
            )

        is_iterable = isinstance(result, Iterable)
        is_single = isinstance(
            result, (str, bytes)
        )

        if is_iterable and not is_single:
            for instance in flatten_list(value=result):
                call_task(instance=instance)
        else:
            call_task(instance=result)

    return handler_index_by_related_instance


def handler_factory_index_related_instance_m2m(data):
    serialized_search_model_related_paths = {}

    for key, value in data.items():
        serialized_search_model_related_paths[
            '{}.{}'.format(key._meta.app_label, key._meta.model_name)
        ] = tuple(value)

    def handler_index_related_instance_m2m(sender, **kwargs):
        action = kwargs.get('action')

        if action not in ('post_add', 'pre_remove'):
            return

        instance = kwargs['instance']
        model = kwargs.get('model')

        kwargs = {
            'action': action,
            'instance_app_label': instance._meta.app_label,
            'instance_model_name': instance._meta.model_name,
            'instance_object_id': instance.pk,
            'model_app_label': model._meta.app_label,
            'model_model_name': model._meta.model_name,
            'pk_set': tuple(
                kwargs['pk_set']
            ),
            'serialized_search_model_related_paths': serialized_search_model_related_paths
        }

        task_index_related_instance_m2m.apply_async(
            kwargs=kwargs
        )

    return handler_index_related_instance_m2m


def handler_factory_index_instance(field_name_set=None):
    def handler_index_instance(sender, **kwargs):
        instance = kwargs['instance']

        update_fields = kwargs.get('update_fields')

        if field_name_set and update_fields is not None:
            if field_name_set.isdisjoint(update_fields):
                return

        task_index_instance.apply_async(
            kwargs={
                'app_label': instance._meta.app_label,
                'model_name': instance._meta.model_name,
                'object_id': instance.pk
            }
        )

    return handler_index_instance
