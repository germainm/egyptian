from django.apps import apps

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin

from .literals import (
    COOKIE_NAME_THEME, USER_THEME_SETTING_KEY, USER_THEME_SETTING_NAMESPACE
)
from .settings import setting_theme, setting_theme_user_selection_enabled


class Theme(AppsModuleLoaderMixin):
    _loader_module_name = 'appearance_themes'
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def get_all(cls):
        return sorted(
            cls._registry.values(), key=lambda theme: theme.label
        )

    @classmethod
    def get_choices(cls):
        return [
            (theme.name, theme.label) for theme in cls.get_all()
        ]

    @classmethod
    def get_for_request(cls, request):
        UserSetting = apps.get_model(
            app_label='appearance', model_name='UserSetting'
        )
        name = None

        if setting_theme_user_selection_enabled.value:
            user = getattr(request, 'user', None)

            if user and user.is_authenticated:
                name = UserSetting.objects.do_value_get(
                    key=USER_THEME_SETTING_KEY,
                    namespace=USER_THEME_SETTING_NAMESPACE, user=user
                )
            else:
                name = request.COOKIES.get(COOKIE_NAME_THEME)

        name = name or setting_theme.value

        return cls.get(name=name) or cls.get_default()

    @classmethod
    def get_default(cls):
        for theme in cls.get_all():
            if theme.default:
                return theme

        theme_list = cls.get_all()
        if theme_list:
            return theme_list[0]

    def __init__(self, name, label, stylesheet, stylesheet_rtl=None, default=False):
        self.default = default
        self.label = label
        self.name = name
        self.stylesheet = stylesheet
        self.stylesheet_rtl = stylesheet_rtl or self.get_stylesheet_rtl_default()

        if name in self.__class__._registry:
            raise KeyError(
                'A theme with the name `{}` is already registered.'.format(
                    name
                )
            )

        self.__class__._registry[name] = self

    def get_stylesheet_rtl_default(self):
        head, separator, tail = self.stylesheet.rpartition('/')
        base, dot, extension = tail.partition('.')
        return '{}{}{}.rtl.{}'.format(head, separator, base, extension)

    def __repr__(self):
        return '<Theme: {}>'.format(self.name)

    def __str__(self):
        return str(self.label)
