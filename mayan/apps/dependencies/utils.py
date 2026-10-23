import requests

import mayan
from mayan.apps.views.http import URL

from .exceptions import DependenciesException
from .literals import (
    DEFAULT_HTTP_TIMEOUT, MAYAN_PYPI_NAME, MESSAGE_GREATER_THAN_SERVER,
    MESSAGE_NOT_LATEST, MESSAGE_UNKNOWN_VERSION, MESSAGE_UNEXPECTED_ERROR,
    MESSAGE_UP_TO_DATE, PYPI_URL
)
from .versions import Version


class PyPIClient:
    class ExceptionAheadOfUpstream(DependenciesException):
        def __init__(self, version_local, version_server):
            self.version_local = version_local
            self.version_server = version_server
            self.message = MESSAGE_GREATER_THAN_SERVER % {
                'version_local': self.version_local,
                'version_server': self.version_server
            }

            super().__init__(self.message)

    class ExceptionNotLatestVersion(DependenciesException):
        def __init__(self, version_local, version_server):
            self.version_local = version_local
            self.version_server = version_server
            self.message = MESSAGE_NOT_LATEST % {
                'version_local': self.version_local,
                'version_server': self.version_server
            }

            super().__init__(self.message)

    class ExceptionUnknownLatestVersion(DependenciesException):
        def __init__(self):
            self.message = MESSAGE_UNKNOWN_VERSION

            super().__init__(self.message)

    def __init__(self):
        self.version_local = Version(version_string=mayan.__version__)

    def check_version(self):
        try:
            text_version_upstream = self.get_server_version()
            version_server = Version(version_string=text_version_upstream)
        except Exception:
            raise PyPIClient.ExceptionUnknownLatestVersion
        else:
            version_local = Version(version_string=mayan.__version__)

        if version_local > version_server:
            raise PyPIClient.ExceptionAheadOfUpstream(
                version_local=mayan.__version__,
                version_server=text_version_upstream
            )
        elif version_local < version_server:
            raise PyPIClient.ExceptionNotLatestVersion(
                version_local=mayan.__version__,
                version_server=text_version_upstream
            )

    def check_version_verbose(self):
        try:
            self.check_version()
        except PyPIClient.ExceptionAheadOfUpstream as exception:
            message = str(exception)
        except PyPIClient.ExceptionNotLatestVersion as exception:
            message = str(exception)
        except PyPIClient.ExceptionUnknownLatestVersion as exception:
            message = str(exception)
        except Exception as exception:
            message = MESSAGE_UNEXPECTED_ERROR % {'exception': exception}
        else:
            message = MESSAGE_UP_TO_DATE % {
                'version_local': mayan.__version__
            }

        return message

    def do_request(self):
        path = 'pypi/{}/json/'.format(MAYAN_PYPI_NAME)
        url = URL(
            netloc=PYPI_URL, scheme='https', path=path
        )

        response = requests.get(
            url=url.to_string(), timeout=DEFAULT_HTTP_TIMEOUT
        )
        response.raise_for_status()
        response_json = response.json()

        return response_json

    def get_server_version(self):
        response_json = self.do_request()

        text_version_upstream = response_json['info']['version']

        return text_version_upstream
