from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    FormView, MultipleObjectConfirmActionView
)

from ..forms import SettingForm
from ..icons import icon_setting_edit, icon_setting_revert
from ..literals import MESSAGE_LOCAL_STORAGE_DISABLED
from ..permissions import permission_settings_edit
from ..setting_clusters import setting_cluster
from ..setting_domains.models import SettingDomainModel


class SettingValueEditView(FormView):
    form_class = SettingForm
    view_icon = icon_setting_edit
    view_permission = permission_settings_edit

    def dispatch(self, request, *args, **kwargs):
        if settings.COMMON_DISABLE_LOCAL_STORAGE:
            messages.warning(
                message=MESSAGE_LOCAL_STORAGE_DISABLED, request=self.request
            )

        self.object = self.get_object()

        return super().dispatch(request=request, *args, **kwargs)

    def form_valid(self, form):
        value_deserialized = SettingDomainModel.deserialize_stream(
            stream=form.cleaned_data['value']
        )
        self.object.do_value_pending_set(value=value_deserialized)

        value_error = self.object.value_error

        if value_error is None:
            messages.success(
                message=_(message='Setting updated successfully.'),
                request=self.request
            )
        else:
            self.object.value_error = None

            messages.error(
                message=_(
                    message='Error updating setting; %s'
                ) % value_error, request=self.request
            )

        return super().form_valid(form=form)

    def get_extra_context(self):
        return {
            'hide_link': True,
            'navigation_object_list': ('object', 'setting_namespace'),
            'object': self.object,
            'setting_namespace': self.object.namespace,
            'title': _(message='Edit setting: %s') % self.object
        }

    def get_initial(self):
        return {'setting': self.object}

    def get_object(self):
        return setting_cluster.get_setting(
            global_name=self.kwargs['setting_global_name']
        )

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'namespace_name': self.object.namespace.name},
            viewname='settings:setting_namespace_detail'
        )


class SettingValueRevertView(MultipleObjectConfirmActionView):
    pk_url_kwarg = 'setting_global_name'
    success_message_plural = _(
        message='%(count)d settings value reverted.'
    )
    success_message_single = _(
        message='Value of setting "%(object)s" reverted.'
    )
    success_message_singular = _(message='%(count)d setting value reverted.')
    title_plural = _(
        message='Revert the value of the %(count)d selected settings.'
    )
    title_single = _(message='Revert the value of setting: %(object)s')
    title_singular = _(
        message='Revert the value of %(count)d selected setting.'
    )
    view_icon = icon_setting_revert
    view_permission = permission_settings_edit

    def get_extra_context(self):
        object_list = self.object_list

        result = {
            'message': _(
                message='Unsaved changes will be lost.'
            ),
            'submit_label': _(message='Revert')
        }

        if len(object_list) == 1:
            result['object'] = object_list[0]

        return result

    def get_object_first(self):
        return self.get_object_list()[0]

    def get_object_list(self):
        self.view_mode_single = True
        self.view_mode_multiple = False

        setting = setting_cluster.get_setting(
            global_name=self.kwargs['setting_global_name']
        )

        return (setting,)

    def object_action(self, form, instance):
        instance.do_value_revert()
