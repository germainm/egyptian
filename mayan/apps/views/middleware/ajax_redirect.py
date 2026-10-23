from django.utils.deprecation import MiddlewareMixin

from ..literals import HEADER_NAME_REDIRECT_LOCATION, REDIRECT_STATUS_CODES
from ..utils import request_is_ajax


class AjaxRedirect(MiddlewareMixin):
    def process_response(self, request, response):
        if not request_is_ajax(request=request):
            return response

        status_code = getattr(response, 'status_code', None)

        if status_code not in REDIRECT_STATUS_CODES:
            return response

        location = response.get('Location', None)

        if not location:
            return response

        response[HEADER_NAME_REDIRECT_LOCATION] = location
        del response['Location']

        response.status_code = 200
        response.content = b''

        return response
