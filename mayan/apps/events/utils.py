from django.apps import apps


def event_object_reference_get(
    app_label=None, model_name=None, object_id=None
):
    if not object_id:
        return None

    model = apps.get_model(app_label=app_label, model_name=model_name)

    return model(pk=object_id)
