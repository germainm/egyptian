from django.conf import settings

from mayan.apps.user_management.link_conditions import (
    condition_user_is_not_super_user
)

from .utils import get_context_user


def condition_is_current_user(context, resolved_object):
    if condition_user_is_authenticated(context=context, resolved_object=resolved_object):
        user = get_context_user(context=context)

        if user:
            return resolved_object == user


def condition_not_is_current_user(context, resolved_object):
    return condition_user_is_authenticated(
        context=context, resolved_object=resolved_object
    ) and not condition_is_current_user(
        context=context, resolved_object=resolved_object
    )


def condition_user_is_authenticated(context, resolved_object):
    user = get_context_user(context=context)

    if user:
        return user.is_authenticated


def condition_account_lockout_enabled(context, resolved_object):
    return getattr(settings, 'AXES_ENABLED', True)


def condition_account_lockout_reset_single(context, resolved_object):
    return condition_account_lockout_enabled(
        context=context, resolved_object=resolved_object
    ) and condition_user_is_not_super_user(
        context=context, resolved_object=resolved_object
    )


def _condition_user_has_usable_password_and_can_change_password(user):
    if user.is_authenticated:
        return user.has_usable_password() and not user.user_options.block_password_change
    else:
        return False


def condition_user_has_usable_password_and_can_change_password(context, resolved_object):
    user = context['request'].user

    return _condition_user_has_usable_password_and_can_change_password(
        user=user
    )


def condition_user_has_usable_password_and_can_change_password_and_is_not_admin(context, resolved_object):
    return _condition_user_has_usable_password_and_can_change_password(
        user=resolved_object
    ) and condition_user_is_not_super_user(
        context=context, resolved_object=resolved_object
    )
