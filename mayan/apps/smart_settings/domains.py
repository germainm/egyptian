class SettingDomain:
    label = None
    name = None

    @classmethod
    def do_cache_invalidate(cls):
        return

    @classmethod
    def do_make_persistent(cls, data, kwargs=None):
        pass

    @classmethod
    def do_key_remove(cls, key):
        pass

    @classmethod
    def do_key_revert(cls, key):
        pass

    @classmethod
    def do_key_update_value_pending(cls, key, value):
        pass

    @classmethod
    def do_ready(cls, data):
        pass

    @classmethod
    def do_revert(cls):
        pass


    @classmethod
    def get_key_value(cls, key):
        raise KeyError

    @classmethod
    def get_key_value_pending(cls, key):
        raise KeyError

    @classmethod
    def get_key_value_pending_map(cls):
        return {}
