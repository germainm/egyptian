import json

from django.db import migrations


def get_backend_data(self):
    return json.loads(s=self.backend_data or '{}')


def set_backend_data(self, obj):
    self.backend_data = json.dumps(obj=obj)


def code_update_to_credentials(apps, schema_editor):
    Source = apps.get_model(app_label='sources', model_name='Source')
    StoredCredential = apps.get_model(
        app_label='credentials', model_name='StoredCredential'
    )

    Source.get_backend_data = get_backend_data
    Source.set_backend_data = set_backend_data

    StoredCredential.get_backend_data = get_backend_data
    StoredCredential.set_backend_data = set_backend_data

    alias = schema_editor.connection.alias

    queryset = Source.objects.using(alias=alias).filter(
        backend_path__startswith='mayan.apps.source_emails'
    )

    for obj in queryset:
        obj_backend_data = obj.get_backend_data()

        stored_credential = StoredCredential(
            label='Email source {} credential'.format(obj.pk),
            internal_name='email_source_{}_credential'.format(obj.pk),
            backend_path='mayan.apps.credentials.credential_backends.CredentialBackendUsernamePassword'
        )

        stored_credential.set_backend_data(
            obj={
                'password': obj_backend_data.get('password'),
                'username': obj_backend_data.get('username')
            }
        )
        stored_credential.save(using=alias)

        obj_backend_data.update(
            {'stored_credential_id': stored_credential.pk}
        )
        obj_backend_data.pop('password', None)
        obj_backend_data.pop('username', None)

        obj.set_backend_data(obj=obj_backend_data)
        obj.save(using=alias)


def reverse_code_update_to_credentials(apps, schema_editor):
    Source = apps.get_model(app_label='sources', model_name='Source')
    StoredCredential = apps.get_model(
        app_label='credentials', model_name='StoredCredential'
    )

    Source.get_backend_data = get_backend_data
    Source.set_backend_data = set_backend_data

    StoredCredential.get_backend_data = get_backend_data
    StoredCredential.set_backend_data = set_backend_data

    alias = schema_editor.connection.alias

    queryset = Source.objects.using(alias=alias).filter(
        backend_path__startswith='mayan.apps.source_emails'
    )

    for obj in queryset:
        obj_backend_data = obj.get_backend_data()

        stored_credential = StoredCredential.objects.using(
            alias=alias
        ).get(
            pk=obj_backend_data['stored_credential_id']
        )
        credential_backend_data = stored_credential.get_backend_data()

        obj_backend_data.update(
            {
                'password': credential_backend_data['password'],
                'username': credential_backend_data['username']
            }
        )
        obj_backend_data.pop('stored_credential_id')

        obj.set_backend_data(obj=obj_backend_data)
        obj.save(using=alias)

        stored_credential.delete(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('credentials', '0001_initial'),
        ('source_emails', '0001_update_source_backend_paths')
    ]

    operations = [
        migrations.RunPython(
            code=code_update_to_credentials,
            reverse_code=reverse_code_update_to_credentials
        )
    ]
