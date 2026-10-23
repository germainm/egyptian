from django.conf import settings
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import ConfirmView

from ..icons import icon_setting_cluster_configuration_save
from ..literals import MESSAGE_LOCAL_STORAGE_DISABLED
from ..permissions import permission_settings_edit
from ..setting_clusters import setting_cluster


class SettingClusterConfigurationFileSave(ConfirmView):
    post_action_redirect = reverse_lazy(
        viewname='settings:setting_cluster_namespace_list'
    )
    view_icon = icon_setting_cluster_configuration_save
    view_permission = permission_settings_edit

    def dispatch(self, request, *args, **kwargs):
        if settings.COMMON_DISABLE_LOCAL_STORAGE:
            messages.warning(
                message=MESSAGE_LOCAL_STORAGE_DISABLED, request=self.request
            )

        return super().dispatch(request=request, *args, **kwargs)

    def get_extra_context(self):
        return {
            'message': _(
                message='This will overwrite the content of the '
                'configuration file.'
            ),
            'submit_label': _(message='Save'),
            'title': _(message='Save settings to the configuration file?')
        }

    def view_action(self, form=None):
        setting_cluster.do_make_persistent()

        messages.success(
            message=_(
                message='Settings saved to configuration file successfully.'
            ), request=self.request
        )
