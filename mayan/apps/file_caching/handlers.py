from .tasks import task_cache_prune


def handler_cache_prune_on_maximum_size_decrease(
    sender, instance, created, **kwargs
):
    if created:
        return

    maximum_size_previous = instance._maximum_size_previous

    if maximum_size_previous:
        if instance.maximum_size < maximum_size_previous:
            task_cache_prune.apply_async(
                kwargs={'cache_id': instance.pk}
            )
