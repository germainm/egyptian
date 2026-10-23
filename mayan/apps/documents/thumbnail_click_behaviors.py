from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.thumbnail_click_behaviors import (
    ThumbnailClickBehaviorBackendRouteToView
)


class ThumbnailClickBehaviorBackendRouteToDocument(
    ThumbnailClickBehaviorBackendRouteToView
):
    label = _(message='Document')
    name = 'route_to_document'

    def get_url(self):
        return self.instance.get_absolute_url()
