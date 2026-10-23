from django.templatetags.static import static
from django.utils.translation import get_language_bidi

from mayan.apps.appearance.classes import Theme


class ViewMixinServiceWorkerStylesheet:
    def get_stylesheet_url_list(self):
        theme = Theme.get_for_request(request=self.request)

        if get_language_bidi():
            theme_stylesheet = theme.stylesheet_rtl
        else:
            theme_stylesheet = theme.stylesheet

        url_list = []

        if theme_stylesheet:
            url_list.append(
                static(theme_stylesheet)
            )

        url_list.append(
            static('appearance_bootstrap/css/appearance_bootstrap.css')
        )

        return url_list
