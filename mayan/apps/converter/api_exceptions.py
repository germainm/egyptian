from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException, Throttled

from .classes import AppImageErrorImage
from .literals import IMAGE_ERROR_IMAGE_BUSY, IMAGE_ERROR_REQUEST_THROTTLED


class AppImageBusy(APIException):
    app_image_error_name = IMAGE_ERROR_IMAGE_BUSY
    default_code = 'image_busy'
    default_detail = _(
        message='The image is already being produced. Request it again in '
        'a moment.'
    )
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, code=None, detail=None, wait=None):
        super().__init__(code=code, detail=detail)

        self.wait = wait

        app_image_error_image = AppImageErrorImage.get(
            name=self.app_image_error_name
        )

        self.detail = {
            'app_image_error_image_template': app_image_error_image.render(
                context={'details': self.detail}
            ),
            'detail': self.detail
        }


class AppImageThrottled(Throttled):
    app_image_error_name = IMAGE_ERROR_REQUEST_THROTTLED

    def __init__(self, wait=None, code=None):
        super().__init__(code=code, wait=wait)

        app_image_error_image = AppImageErrorImage.get(
            name=self.app_image_error_name
        )

        self.detail = {
            'app_image_error_image_template': app_image_error_image.render(
                context={'details': self.detail}
            ),
            'detail': self.detail
        }
