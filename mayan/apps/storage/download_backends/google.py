from google.cloud import storage

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .base import DownloadBackend


class DownloadBackendGoogleCloudStorageSignedURL(DownloadBackend):
    DEFAULT_EXPIRATION = 3600

    def __init__(
        self, bucket_name, stored_credential_internal_name, expiration=None
    ):
        self.bucket_name = bucket_name
        self.stored_credential_internal_name = stored_credential_internal_name

        if not expiration:
            expiration = self.DEFAULT_EXPIRATION

        self.expiration = expiration

    def get_download_file_object(self, obj):
        StoredCredential = apps.get_model(
            app_label='credentials', model_name='StoredCredential'
        )

        stored_credential = StoredCredential.objects.get(
            internal_name=self.stored_credential_internal_name
        )

        stored_credential_data = stored_credential.get_backend_data()

        storage_client = storage.Client.from_service_account_info(
            info=stored_credential_data
        )

        bucket = storage_client.bucket(bucket_name=self.bucket_name)

        filename = self.get_stored_filename(obj=obj)
        blob = bucket.blob(blob_name=filename)

        return blob.generate_signed_url(
            expiration=self.expiration, method='GET', version='v4'
        )

    def get_download_filename(self, obj):
        super_filename = super().get_download_filename(obj=obj)
        return 'signed-url-for-{}'.format(super_filename)

    def get_stored_filename(self, obj):
        raise ImproperlyConfigured(
            'Class `{}` must provide a `get_stored_filename` method '
            'that returns the storage filename.'.format(
                self.__class__.__name__
            )
        )
