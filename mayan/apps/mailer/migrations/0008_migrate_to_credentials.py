import json

from django.db import migrations


def get_backend_data(self):
    return json.loads(s=self.backend_data or '{}')


def set_backend_data(self, obj):
    self.backend_data = json.dumps(obj=obj)


def code_update_to_credentials(apps, schema_editor):
    UserMailer = apps.get_model(app_label='mailer', model_name='UserMailer')
    StoredCredential = apps.get_model(
        app_label='credentials', model_name='StoredCredential'
    )

    UserMailer.get_backend_data = get_backend_data
    UserMailer.set_backend_data = set_backend_data

    StoredCredential.get_backend_data = get_backend_data
    StoredCredential.set_backend_data = set_backend_data

    alias = schema_editor.connection.alias

    queryset = UserMailer.objects.using(alias=alias).filter(
        backend_path='mayan.apps.mailer.mailers.DjangoSMTP'
    )

    for obj in queryset:
        obj_backend_data = obj.get_backend_data()

        stored_credential = StoredCredential(
            label='SMTP mailer {} credential'.format(obj.pk),
            internal_name='mailer_smtp_{}_credential'.format(obj.pk),
            backend_path='mayan.apps.credentials.credential_backends.CredentialBackendUsernamePassword'
        )

        stored_credential.set_backend_data(
            obj={
                'password': obj_backend_data['password'],
                'username': obj_backend_data['username']
            }
        )
        stored_credential.save(using=alias)

        obj_backend_data.update(
            {'stored_credential_id': stored_credential.pk}
        )
        obj_backend_data.pop('password')
        obj_backend_data.pop('username')

        obj.set_backend_data(obj=obj_backend_data)
        obj.save(using=alias)


def reverse_code_update_to_credentials(apps, schema_editor):
    UserMailer = apps.get_model(app_label='mailer', model_name='UserMailer')
    StoredCredential = apps.get_model(
        app_label='credentials', model_name='StoredCredential'
    )

    UserMailer.get_backend_data = get_backend_data
    UserMailer.set_backend_data = set_backend_data

    StoredCredential.get_backend_data = get_backend_data
    StoredCredential.set_backend_data = set_backend_data

    alias = schema_editor.connection.alias

    queryset = UserMailer.objects.using(alias=alias).filter(
        backend_path='mayan.apps.mailer.mailers.DjangoSMTP'
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
        ('mailer', '0007_auto_20200616_0722')
    ]

    operations = [
        migrations.RunPython(
            code=code_update_to_credentials,
            reverse_code=reverse_code_update_to_credentials
        )
    ]
