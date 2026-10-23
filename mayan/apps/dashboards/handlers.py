from .classes import Dashboard


def handler_dashboard_initialize(**kwargs):
    Dashboard.load_modules()
