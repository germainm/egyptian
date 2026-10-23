def get_server_supports_concurrency(environ):
    if environ.get('wsgi.multithread', False):
        return True

    return get_gevent_is_active()


def get_gevent_is_active():
    try:
        from gevent import monkey
    except ImportError:
        return False

    return monkey.is_module_patched('socket')
