from django.apps import apps
from django.db.utils import OperationalError, ProgrammingError


def update_cache_maximum_size(defined_storage_name, maximum_size):
    Cache = apps.get_model(
        app_label='file_caching', model_name='Cache'
    )

    try:
        cache = Cache.objects.get(
            defined_storage_name=defined_storage_name
        )
    except (Cache.DoesNotExist, OperationalError, ProgrammingError):
        """
        Non fatal. Either a non initialized installation, where the table
        does not exist yet, or an installation where the `post_migrate`
        handler of the app owning the cache has not created the instance
        yet. In both cases the handler sets the maximum size when it runs,
        so there is nothing to update here.
        """
    else:
        is_at_target = cache.maximum_size == maximum_size
        is_consistent = cache.maximum_size_old == cache.maximum_size

        if not is_at_target or not is_consistent:
            cache.maximum_size = maximum_size
            cache.save()
