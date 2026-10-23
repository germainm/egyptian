class SourceException(Exception):
    pass


class SourceActionException(SourceException):
    pass


class SourceActionExceptionRejected(SourceActionException):
    pass


class SourceActionExceptionUnknown(SourceActionException):
    pass


class SourceActionExceptionInterface(SourceActionException):
    pass


class SourceActionExceptionInterfaceArgumentMissing(SourceActionExceptionInterface):
    pass


class SourceActionExceptionInterfaceUnknown(SourceActionExceptionInterface):
    pass
