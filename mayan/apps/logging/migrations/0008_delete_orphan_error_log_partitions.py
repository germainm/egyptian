from django.db import migrations


def code_orphan_error_log_partition_delete(apps, schema_editor):
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )
    ErrorLogPartition = apps.get_model(
        app_label='logging', model_name='ErrorLogPartition'
    )

    alias = schema_editor.connection.alias

    queryset_partition = ErrorLogPartition.objects.using(alias=alias)

    content_type_id_list = queryset_partition.values_list(
        'content_type', flat=True
    ).distinct()

    for content_type_id in content_type_id_list:
        content_type = ContentType.objects.using(alias=alias).get(
            pk=content_type_id
        )

        queryset_orphan = queryset_partition.filter(
            content_type=content_type_id
        )

        try:
            model = apps.get_model(
                app_label=content_type.app_label,
                model_name=content_type.model
            )
        except LookupError:
            queryset_orphan.delete()
        else:
            queryset_object_id = model._default_manager.using(
                alias=alias
            ).values('pk')

            queryset_orphan = queryset_orphan.exclude(
                object_id__in=queryset_object_id
            )

            queryset_orphan.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('logging', '0007_errorlogpartitionentry_domain_name')
    ]

    operations = [
        migrations.RunPython(
            code=code_orphan_error_log_partition_delete, elidable=True,
            reverse_code=migrations.RunPython.noop
        )
    ]
