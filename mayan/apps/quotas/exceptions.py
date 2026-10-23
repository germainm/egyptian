class QuotaBaseException(Exception):
    pass


class QuotaExceeded(QuotaBaseException):
    pass
