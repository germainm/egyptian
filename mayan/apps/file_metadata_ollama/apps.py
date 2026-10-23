from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class FileMetadataOllamaApp(MayanAppConfig):
    app_namespace = 'file_metadata_ollama'
    app_url = 'file_metadata_ollama'
    has_tests = True
    name = 'mayan.apps.file_metadata_ollama'
    verbose_name = _(message='File metadata Ollama')
