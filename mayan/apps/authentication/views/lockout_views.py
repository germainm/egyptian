from django.contrib import messages
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.user_management.querysets import get_user_queryset
from mayan.apps.views.generics import MultipleObjectConfirmActionView

from ..events import event_user_account_lockout_reset
from ..icons import icon_account_lockout_reset
from ..lockouts import reset_user_lockout
from ..permissions import permission_account_lockout_reset


class UserAccountLockoutResetView(MultipleObjectConfirmActionView):
    object_permission = permission_account_lockout_reset
    pk_url_kwarg = 'user_id'
    source_queryset = get_user_queryset()
    success_message = _(
        message='Account lockout reset for %(count)d user.'
    )
    success_message_plural = _(
        message='Account lockout reset for %(count)d users.'
    )
    view_icon = icon_account_lockout_reset

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'title': ngettext(
                singular='Reset account lockout for %(count)d user?',
                plural='Reset account lockout for %(count)d users?',
                number=queryset.count()
            ) % {
                'count': queryset.count()
            }
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Reset account lockout for user: %s'
                    ) % queryset.first()
                }
            )

        return result

    def object_action(self, instance, form=None):
        try:
            reset_user_lockout(user=instance)
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error resetting account lockout for user '
                    '"%(user)s": %(error)s'
                ) % {
                    'error': exception, 'user': instance
                }, request=self.request
            )
        else:
            event_user_account_lockout_reset.commit(
                actor=self.request.user, target=instance
            )
