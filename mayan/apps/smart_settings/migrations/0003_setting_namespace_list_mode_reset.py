from django.db import migrations

VIEW_NAME_SETTING_NAMESPACE_DETAIL = 'settings:setting_namespace_detail'


def code_setting_namespace_list_mode_reset(apps, schema_editor):
    UserViewMode = apps.get_model(
        app_label='views', model_name='UserViewMode'
    )

    UserViewMode.objects.using(
        alias=schema_editor.connection.alias
    ).filter(name=VIEW_NAME_SETTING_NAMESPACE_DETAIL).delete()


def code_setting_namespace_list_mode_reset_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('smart_settings', '0002_updatedstoredsetting_delete_updatedsetting'),
        ('views', '0002_userconfirmview')
    ]

    operations = [
        migrations.RunPython(
            code=code_setting_namespace_list_mode_reset,
            reverse_code=code_setting_namespace_list_mode_reset_reverse
        )
    ]
