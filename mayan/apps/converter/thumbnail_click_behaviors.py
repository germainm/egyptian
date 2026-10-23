from django.template import loader
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.classes import BaseBackend


class ThumbnailClickBehaviorBackend(BaseBackend):
    _backend_identifier = 'name'
    _loader_module_name = 'thumbnail_click_behaviors'
    label = None
    name = None
    template_name = None

    @classmethod
    def get_setting_choices(cls):
        backend_list = cls.get_all()

        name_list = [
            backend.backend_id for backend in backend_list if backend.is_visible
        ]
        name_list.sort()

        return name_list

    @classmethod
    def register(cls, klass):
        name = klass.name

        if name is not None:
            super().register(klass=klass)

    def __init__(
        self, instance, object_image_data, container_class=None,
        disable_title_link=False, display_full_height=False,
        display_height=None, gallery_name=None, image_alt=None,
        image_template_name=None
    ):
        self.container_class = container_class
        self.disable_title_link = disable_title_link
        self.display_full_height = display_full_height
        self.display_height = display_height
        self.gallery_name = gallery_name
        self.image_alt = image_alt
        self.image_template_name = image_template_name
        self.instance = instance
        self.object_image_data = object_image_data

    def get_anchor_context(self):
        return {}

    def get_render_context(self):
        render_context = {
            'container_class': self.container_class,
            'disable_title_link': self.disable_title_link,
            'display_full_height': self.display_full_height,
            'display_height': self.display_height,
            'image_alt': self.image_alt,
            'image_template_name': self.image_template_name,
            'instance': self.instance,
            'object_image_data': self.object_image_data
        }

        anchor_context = self.get_anchor_context()
        render_context.update(anchor_context)

        return render_context

    def render(self):
        render_context = self.get_render_context()

        return loader.render_to_string(
            context=render_context, template_name=self.template_name
        )


class ThumbnailClickBehaviorBackendRouteToView(ThumbnailClickBehaviorBackend):
    template_name = 'converter/thumbnail_click_behaviors/route_to_view.html'

    def get_anchor_context(self):
        return {
            'url': self.get_url()
        }

    def get_url(self):
        raise NotImplementedError(
            'Subclasses must implement the `get_url` method.'
        )


class ThumbnailClickBehaviorBackendImagePreview(ThumbnailClickBehaviorBackend):
    label = _(message='Image preview')
    name = 'image_preview'
    template_name = 'converter/thumbnail_click_behaviors/image_preview.html'

    def get_anchor_context(self):
        return {'gallery_name': self.gallery_name}
