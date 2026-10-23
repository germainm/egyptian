import logging
from pathlib import Path

from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _

from mayan.apps.sources.exceptions import SourceException

from ..classes import SourceStoredFile

logger = logging.getLogger(name=__name__)


class SourceBackendMixinStoredFileLocationFilesystem:
    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'folder_path': {
                    'class': 'django.forms.CharField',
                    'default': '',
                    'help_text': _(
                        message='Server side filesystem path.'
                    ),
                    'kwargs': {
                        'max_length': 255,
                    },
                    'label': _(message='Folder path'),
                    'required': True
                },
                'include_subdirectories': {
                    'class': 'django.forms.BooleanField',
                    'default': '',
                    'help_text': _(
                        message='If checked, not only will the folder path be '
                        'scanned for files but also its subdirectories.'
                    ),
                    'label': _(message='Include subdirectories?'),
                    'required': False
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Storage'), {
                    'fields': ('folder_path', 'include_subdirectories')
                }
            ),
        )

        return fieldsets

    def get_storage_backend_arguments(self):
        return {
            'location': '{}'.format(
                self.kwargs['folder_path']
            )
        }

    def get_storage_backend_class(self):
        return FileSystemStorage

    def get_storage_backend_instance(self):
        storage_backend_arguments = self.get_storage_backend_arguments()
        storage_backend_class = self.get_storage_backend_class()

        try:
            return storage_backend_class(**storage_backend_arguments)
        except Exception as exception:
            message = _(
                message='Unable to initialize storage; %s'
            ) % exception

            logger.fatal(message)
            raise TypeError(message) from exception

    def get_stored_file_list(self):
        path = Path(
            self.kwargs['folder_path']
        )

        path.lstat()
        if not path.is_dir():
            raise SourceException(
                'Path {} is not a directory.'.format(path)
            )

        regex_exclude = self.get_regex_exclude()
        regex_include = self.get_regex_include()

        include_subdirectories = self.kwargs.get(
            'include_subdirectories', False
        )

        try:
            if include_subdirectories:
                iterator = path.rglob(pattern='*')
            else:
                iterator = path.glob(pattern='*')

            for entry in iterator:
                if entry.is_file():
                    if regex_include.match(string=entry.name) and not regex_exclude.match(string=entry.name):
                        relative_filename = str(
                            entry.relative_to(
                                self.kwargs['folder_path']
                            )
                        )
                        yield SourceStoredFile(
                            filename=relative_filename, source=self
                        )
        except Exception as exception:
            message = 'Unable get list of files from source: {}; {}'.format(
                self, exception
            )

            logger.error(message)
            raise ValueError(message) from exception
