class LockManagerError(Exception):
    pass


class LockError(LockManagerError):
    pass


class LockBackendError(LockError):
    pass
