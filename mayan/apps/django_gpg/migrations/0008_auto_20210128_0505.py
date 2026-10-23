from datetime import datetime

from django.db import migrations
from django.utils.encoding import force_str
from django.utils.timezone import make_aware

from ..classes import GPGBackend


def code_save_keys(apps, schema_editor):
    Key = apps.get_model(
        app_label='django_gpg', model_name='Key'
    )

    for key in Key.objects.using(alias=schema_editor.connection.alias).all():
        key_data = force_str(s=key.key_data)
        import_results, key_info = GPGBackend.get_instance().import_and_list_keys(
            key_data=key_data
        )

        key.creation_date = make_aware(
            value=datetime.fromtimestamp(
                int(
                    key_info['date']
                )
            )
        )
        if key_info['expires']:
            key.expiration_date = make_aware(
                value=datetime.fromtimestamp(
                    int(
                        key_info['expires']
                    )
                )
            )
        key.save()


def code_save_keys_reverse(apps, schema_editor):
    Key = apps.get_model(
        app_label='django_gpg', model_name='Key'
    )

    for key in Key.objects.using(alias=schema_editor.connection.alias).all():
        key_data = force_str(s=key.key_data)
        import_results, key_info = GPGBackend.get_instance().import_and_list_keys(
            key_data=key_data
        )

        key.creation_date = make_aware(
            value=datetime.fromtimestamp(
                int(
                    key_info['date']
                )
            )
        ).date()
        if key_info['expires']:
            key.expiration_date = make_aware(
                value=datetime.fromtimestamp(
                    int(
                        key_info['expires']
                    )
                )
            ).date()
        key.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_gpg', '0007_auto_20210128_0504')
    ]

    operations = [
        migrations.RunPython(
            code=code_save_keys,
            reverse_code=code_save_keys_reverse
        )
    ]
