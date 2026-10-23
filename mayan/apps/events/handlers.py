from django.apps import apps


def handler_stored_event_type_pk_cache_clear(sender, **kwargs):
    StoredEventType = apps.get_model(
        app_label='events', model_name='StoredEventType'
    )

    StoredEventType.objects.do_pk_cache_clear()


def handler_delete_object_events(sender, instance, **kwargs):
    Action = apps.get_model(app_label='actstream', model_name='Action')
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )

    content_type = ContentType.objects.get_for_model(model=instance)

    queryset = Action.objects.filter(
        target_content_type=content_type, target_object_id=str(instance.pk)
    )
    queryset.delete()
