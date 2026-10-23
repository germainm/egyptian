from django.conf import settings

from .literals import AUTHENTICATION_LOCKOUT_SETTING_AXES_MAP


def callback_lockout_update(setting):
    key = AUTHENTICATION_LOCKOUT_SETTING_AXES_MAP[setting.global_name]
    setattr(settings, key, setting.value)
