class AppManagerException(Exception):
    pass


class InitializationStepError(AppManagerException):
    pass


class InitializationStepPreconditionError(AppManagerException):
    pass
