from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class FormsApp(MayanAppConfig):
    app_namespace = 'forms'
    app_url = 'forms'
    has_javascript_translations = True
    has_static_media = True
    has_tests = True
    label = 'mayan_forms'
    name = 'mayan.apps.forms'
    static_media_ignore_patterns = (
        'mayan_forms/node_modules/dropzone/index.js',
        'mayan_forms/node_modules/dropzone/component.json'
    )
    verbose_name = _(message='Forms')
