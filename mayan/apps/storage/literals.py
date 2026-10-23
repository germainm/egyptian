import os
import tempfile

from django.conf import settings

BUFFERED_FILE_SEEK_BLOCK_SIZE = 64 * 1024

COMMAND_NAME_STORAGE_PROCESS = 'storage_process'
COMMAND_NAME_STORAGE_SHARD_FILES = 'storage_shard_files'

DEFAULT_DOWNLOAD_FILE_EXPIRATION_INTERVAL = 60 * 24 * 2
DEFAULT_SHARED_UPLOADED_FILE_EXPIRATION_INTERVAL = 60 * 60 * 24 * 7
DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
DEFAULT_STORAGE_DOWNLOAD_FILE_STORAGE_ARGUMENTS = {
    'location': os.path.join(settings.MEDIA_ROOT, 'download_files')
}
DEFAULT_STORAGE_SHARED_STORAGE = 'django.core.files.storage.FileSystemStorage'
DEFAULT_STORAGE_SHARED_STORAGE_ARGUMENTS = {
    'location': os.path.join(settings.MEDIA_ROOT, 'shared_files')
}
DEFAULT_STORAGE_TEMPORARY_DIRECTORY = tempfile.gettempdir()

DEFAULT_STORAGE_BACKEND = 'django.core.files.storage.FileSystemStorage'

DEFAULT_STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM = 100
DEFAULT_STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM = 1024 * 1024 * 1024
DEFAULT_STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM = 256 * 1024 * 1024

MIME_TYPE_EML = ('message/rfc822', 'text/plain')
MSG_MIME_TYPES = (
    'application/vnd.ms-outlook', 'application/vnd.ms-office',
    'application/x-ole-storage'
)
STORAGE_NAME_DOWNLOAD_FILE = 'storage__downloadfile'
STORAGE_NAME_SHARED_UPLOADED_FILE = 'storage__shareduploadedfile'
TASK_DOWNLOAD_FILE_STALE_INTERVAL = 60 * 10
TASK_SHARED_UPLOADS_STALE_INTERVAL = 60 * 10
