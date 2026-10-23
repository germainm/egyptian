from django.core.cache import caches

from rest_framework import throttling

from .settings import (
    setting_throttling_enabled, setting_throttling_rate_anonymous,
    setting_throttling_rate_user
)


class MayanAnonRateThrottle(throttling.AnonRateThrottle):
    cache = caches['rest_api_throttling']

    def get_rate(self):
        if not setting_throttling_enabled.value:
            return None

        return setting_throttling_rate_anonymous.value or None


class MayanUserRateThrottle(throttling.UserRateThrottle):
    cache = caches['rest_api_throttling']

    def get_rate(self):
        if not setting_throttling_enabled.value:
            return None

        return setting_throttling_rate_user.value or None
