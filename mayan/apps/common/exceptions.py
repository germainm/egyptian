class BaseCommonException(Exception):
    pass


class ResolverError(Exception):
    pass


class ResolverPipelineError(Exception):
    pass


class NonUniqueError(BaseCommonException):
    pass
