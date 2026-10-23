import re

from django.utils.translation import gettext_lazy as _

COMMAND_NAME_DEPENDENCIES_CHECK_VERSION = 'dependencies_check_version'
COMMAND_NAME_DEPENDENCIES_GENERATE_REQUIREMENTS = 'dependencies_generate_requirements'
COMMAND_NAME_DEPENDENCIES_INSTALL = 'dependencies_install'
COMMAND_NAME_DEPENDENCIES_SHOW_VERSION = 'dependencies_show_version'

DEFAULT_DEPENDENCIES_GOOGLE_FONTS_URL = 'https://fonts.googleapis.com'
DEFAULT_DEPENDENCIES_NPM_REGISTRY_URL = 'https://registry.npmjs.com'
DEFAULT_HTTP_TIMEOUT = (10, 30)

MAYAN_PYPI_NAME = 'mayan-edms'

MESSAGE_GREATER_THAN_SERVER = _(
    message='Your version (%(version_local)s), is more recent than the published '
    'version (%(version_server)s).'
)
MESSAGE_NOT_LATEST = _(
    message='The version you are using (%(version_local)s) is '
    'outdated. The latest version is %(version_server)s.'
)
MESSAGE_REQUIREMENTS_CHECK_PATH_MISSING = _(
    message='Checking compares the requirement files against the declared '
    'dependencies and there are no files to compare without `--path`.'
)
MESSAGE_REQUIREMENTS_DESTINATION_MISSING = _(
    message='Generating the requirements of every environment writes files '
    'and has no single stream to print to. Pass `--path` with the directory '
    'the requirement files are written to, or name a single environment to '
    'print it instead.'
)
MESSAGE_REQUIREMENTS_FILE_OUTDATED = _(
    message='The requirement file `%(filename)s` does not match the '
    'dependencies declared for the `%(environment)s` environment.'
)
MESSAGE_REQUIREMENTS_OUTDATED = _(
    message='Outdated requirement files: %(filename_list)s. Regenerate them '
    'with `make python-requirements-generate` and commit the result.'
)
MESSAGE_REQUIREMENTS_UNKNOWN_ENVIRONMENT = _(
    message='Unknown dependency environment `%(environment)s`. The known '
    'environments are: %(environment_list)s.'
)
MESSAGE_UNEXPECTED_ERROR = _(
    message='Unexpected error trying to determine the latest version available. '
    'Make sure your installation has a connection to the internet; '
    '%(exception)s'
)
MESSAGE_UNKNOWN_VERSION = _(
    message='It is not possible to determine the latest version available.'
)

MESSAGE_UP_TO_DATE = 'Your version (%(version_local)s), is up-to-date.'

PYPI_URL = 'pypi.org'

REGULAR_EXPRESSION_CSS_URL = re.compile(pattern=r'url\((.*?)\)')
