from django.apps import apps


def initializer_setup_periodic_tasks():
    Source = apps.get_model(
        app_label='sources', model_name='Source'
    )

    for source in Source.objects.filter(enabled=True):
        backend_instance = source.get_backend_instance()
        backend_instance.update()
