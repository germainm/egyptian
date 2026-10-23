from django.apps import apps


def initializer_purge_permissions():
    StoredPermission = apps.get_model(
        app_label='permissions', model_name='StoredPermission'
    )

    StoredPermission.objects.purge_obsolete()
