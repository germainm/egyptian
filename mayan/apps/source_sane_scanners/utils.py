from mayan.apps.sources.settings import setting_backend_arguments

from .literals import DEFAULT_BINARY_SCANIMAGE_PATH


def get_command_path_scanimage(dotted_name):
    backend_arguments = setting_backend_arguments.value

    keyword_arguments = backend_arguments.get(dotted_name, {})

    return keyword_arguments.get(
        'scanimage_path', DEFAULT_BINARY_SCANIMAGE_PATH
    )
