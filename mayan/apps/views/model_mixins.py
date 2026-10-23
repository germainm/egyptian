from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .literals import LIST_MODE_CHOICES


class ModelMixinAppConfig:
    def get_app_config(self):
        app_config = MayanAppConfig.get_by_namespace(namespace=self.namespace)

        return app_config

    get_app_config.help_text = _(message='The app to which the view belongs.')
    get_app_config.short_description = _(message='App')

    def get_app_config_verbose_name(self):
        try:
            app_config = self.get_app_config()
        except KeyError:
            return None

        return app_config.verbose_name

    get_app_config_verbose_name.help_text = _(
        message='The app to which the view belongs.'
    )
    get_app_config_verbose_name.short_description = _(message='App')


class ModelMixinUserConfirmViewBusinessLogic(ModelMixinAppConfig):
    pass


class ModelMixinUserViewModeBusinessLogic(ModelMixinAppConfig):
    def get_value_display(self):
        map_list_mode_choices = dict(LIST_MODE_CHOICES)

        try:
            return map_list_mode_choices[self.value]
        except KeyError:
            return _(message='Unknown mode: %s') % self.value

    get_value_display.help_text = _(message='The current mode of the view.')
    get_value_display.short_description = _(message='Value')
