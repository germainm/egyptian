from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import View

from mayan.apps.views.view_mixins import (
    MultipleObjectViewMixin, RestrictedQuerysetViewMixin, SingleObjectMixin,
    ViewPermissionCheckViewMixin
)

from .mixins import (
    ViewMixinBackendDownload, ViewMixinDownload, ViewMixinDownloadEvent
)


class ViewBaseDownload(
    ViewMixinDownload, ViewPermissionCheckViewMixin, View
):
    def get(self, request, *args, **kwargs):
        return self.render_to_response()


class ViewMultipleObjectDownload(
    RestrictedQuerysetViewMixin, MultipleObjectViewMixin, ViewBaseDownload
):
    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != ViewMultipleObjectDownload.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def get_queryset(self):
        try:
            return super().get_queryset()
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            return super().get_queryset()


class ViewSingleObjectDownload(
    ViewMixinDownloadEvent, RestrictedQuerysetViewMixin, SingleObjectMixin,
    ViewBaseDownload
):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request=request, *args, **kwargs)

    def get_download_file_object(self):
        return self.object.open(mode='rb')

    def get_download_filename(self):
        return str(self.object)

    def get_download_event_target(self):
        return self.object


class ViewSingleObjectBackendDownload(
    ViewMixinBackendDownload, ViewSingleObjectDownload
):
    pass
