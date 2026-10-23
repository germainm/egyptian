class GPGException(Exception):
    pass


class DecryptionError(GPGException):
    pass


class KeyFetchingError(GPGException):
    pass


class KeyDoesNotExist(GPGException):
    pass


class NeedPassphrase(GPGException):
    pass


class PassphraseError(GPGException):
    pass


class VerificationError(GPGException):
    pass
