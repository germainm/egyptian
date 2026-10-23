from .utils import purge_periodic_tasks


def initializer_perform_upgrade():
    purge_periodic_tasks()
