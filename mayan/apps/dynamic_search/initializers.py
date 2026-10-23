from .search_backends import SearchBackend


def initializer_search_backend_initialize():
    backend = SearchBackend.get_instance()

    backend.initialize()


def initializer_search_backend_upgrade():
    backend = SearchBackend.get_instance()

    backend.upgrade()
