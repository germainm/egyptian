from .classes import Permission


def handler_permission_initialize(**kwargs):
    Permission.load_modules()
