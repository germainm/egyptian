from django.apps import apps

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin

from .literals import (
    COOKIE_NAME_COLOR_MODE, USER_COLOR_MODE_SETTING_KEY,
    USER_COLOR_MODE_SETTING_NAMESPACE
)
from .settings import (
    setting_color_mode, setting_color_mode_user_selection_enabled
)


class ColorMode(AppsModuleLoaderMixin):
    _loader_module_name = 'bootstrap_color_modes'
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def get_all(cls):
        return sorted(
            cls._registry.values(), key=lambda color_mode: color_mode.label
        )

    @classmethod
    def get_choices(cls):
        return [
            (color_mode.name, color_mode.label) for color_mode in cls.get_all()
        ]

    @classmethod
    def get_default(cls):
        for color_mode in cls.get_all():
            if color_mode.default:
                return color_mode

        color_mode_list = cls.get_all()
        if color_mode_list:
            return color_mode_list[0]

    @classmethod
    def get_for_request(cls, request):
        UserSetting = apps.get_model(
            app_label='appearance', model_name='UserSetting'
        )
        name = None

        if setting_color_mode_user_selection_enabled.value:
            user = getattr(request, 'user', None)

            if user and user.is_authenticated:
                name = UserSetting.objects.do_value_get(
                    key=USER_COLOR_MODE_SETTING_KEY,
                    namespace=USER_COLOR_MODE_SETTING_NAMESPACE, user=user
                )
            elif request is not None:
                name = request.COOKIES.get(COOKIE_NAME_COLOR_MODE)

        name = name or setting_color_mode.value

        return cls.get(name=name) or cls.get_default()

    def __init__(self, name, label, default=False, theme_color=None):
        self.default = default
        self.label = label
        self.name = name
        self.theme_color = theme_color

        if name in self.__class__._registry:
            raise KeyError(
                'A color mode with the name `{}` is already '
                'registered.'.format(name)
            )

        self.__class__._registry[name] = self

    def __repr__(self):
        return '<ColorMode: {}>'.format(self.name)

    def __str__(self):
        return str(self.label)
