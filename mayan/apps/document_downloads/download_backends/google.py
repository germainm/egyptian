from mayan.apps.storage.download_backends.google import (
    DownloadBackendGoogleCloudStorageSignedURL
)

from .mixins import DownloadBackendMixinDocumentFile


class DownloadBackendDocumentFileGoogleCloudStorageSignedURL(
    DownloadBackendMixinDocumentFile,
    DownloadBackendGoogleCloudStorageSignedURL
):
    pass
