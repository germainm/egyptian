from django.core.exceptions import ImproperlyConfigured
from django.http.response import FileResponse
from django.utils.decorators import classonlymethod

from mayan.apps.mime_types.classes import MIMETypeBackend

from ..download_backends.base import DownloadBackend


class ViewMixinBackendDownload:
    backend_arguments = None
    backend_path = None

    @classonlymethod
    def as_view(cls, **initkwargs):
        try:
            cls.get_backend_instance()
        except ImportError as exception:
            raise ImproperlyConfigured(
                'The download view `{}` was not able to load download '
                'backend `{}`. Ensure the download backend path and the '
                'arguments are correct.'.format(
                    cls.__name__, cls.get_backend_path()
                )
            ) from exception

        return super().as_view(**initkwargs)

    @classmethod
    def get_backend_arguments(cls):
        return cls.backend_arguments

    @classmethod
    def get_backend_instance(cls):
        arguments = cls.get_backend_arguments()
        dotted_path = cls.get_backend_path()

        return DownloadBackend.get_backend_instance(
            dotted_path=dotted_path, arguments=arguments
        )

    @classmethod
    def get_backend_path(cls):
        return cls.backend_path

    def get(self, request, *args, **kwargs):
        self.download_backend_instance = self.get_backend_instance()

        return super().get(request=request, *args, **kwargs)

    def get_download_file_object(self):
        return self.download_backend_instance.get_download_file_object(
            obj=self.get_object()
        )

    def get_download_filename(self):
        return self.download_backend_instance.get_download_filename(
            obj=self.get_object()
        )

    def get_download_mime_type_and_encoding(self, file_object):
        mime_type, encoding = self.download_backend_instance.get_download_mime_type_and_encoding(
            obj=self.get_object()
        )

        return (mime_type, encoding)


class ViewMixinDownload:
    as_attachment = True

    def get_as_attachment(self):
        return self.as_attachment

    def get_download_file_object(self):
        raise ImproperlyConfigured(
            'View `{}` must provide a `get_download_file_object` method '
            'that returns a file like object.'.format(
                self.__class__.__name__
            )
        )

    def get_download_filename(self):
        return None

    def get_download_mime_type_and_encoding(self, file_object):
        backend_instance = MIMETypeBackend.get_backend_instance()
        mime_type, encoding = backend_instance.get_mime_type(
            file_object=file_object, mime_type_only=True
        )

        return (mime_type, encoding)

    def render_to_response(self):
        response = FileResponse(
            as_attachment=self.get_as_attachment(),
            filename=self.get_download_filename(),
            streaming_content=self.get_download_file_object()
        )

        encoding_map = {
            'bzip2': 'application/x-bzip',
            'gzip': 'application/gzip',
            'xz': 'application/x-xz'
        }

        if response.file_to_stream:
            mime_type, encoding = self.get_download_mime_type_and_encoding(
                file_object=response.file_to_stream
            )
            content_type = encoding_map.get(encoding, mime_type)
            response.headers['Content-Type'] = content_type or 'application/octet-stream'
        else:
            response.headers['Content-Type'] = 'application/octet-stream'

        return response


class ViewMixinDownloadEvent:
    download_event_type = None

    def get_download_event_action_object(self):
        return None

    def get_download_event_actor(self):
        return self.request.user

    def get_download_event_target(self):
        return None

    def get_download_event_type(self):
        return self.download_event_type

    def render_to_response(self):
        event_type = self.get_download_event_type()

        if event_type:
            event_type.commit(
                action_object=self.get_download_event_action_object(),
                actor=self.get_download_event_actor(),
                target=self.get_download_event_target()
            )

        return super().render_to_response()
