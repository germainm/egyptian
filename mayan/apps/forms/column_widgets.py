from mayan.apps.navigation.column_widgets import SourceColumnWidget

from .icons import icon_fail as default_icon_fail, icon_ok as default_icon_ok


class TwoStateWidget(SourceColumnWidget):
    template_name = 'forms/two_state_widget.html'

    def __init__(self, icon_ok=None, icon_fail=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_ok = icon_ok or default_icon_ok
        self.icon_fail = icon_fail or default_icon_fail

    def get_extra_context(self):
        return {
            'icon_fail': self.icon_fail, 'icon_ok': self.icon_ok
        }


class ObjectLinkWidget(SourceColumnWidget):
    template_name = 'forms/object_link_widget.html'

    def get_extra_context(self):
        label = ''
        object_type = ''
        url = None

        if self.value:
            label = str(self.value)
            try:
                object_type = '{}: '.format(self.value._meta.verbose_name)
            except AttributeError:
                object_type = ''

            try:
                url = self.value.get_absolute_url()
            except AttributeError:
                url = None

            if getattr(self.value, 'is_staff', None) or getattr(self.value, 'is_superuser', None):
                url = '#'

        return {
            'label': label, 'object_type': object_type,
            'url': url or '#'
        }
