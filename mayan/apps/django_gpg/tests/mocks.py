from .literals import TEST_RECEIVE_KEY, TEST_SEARCH_FINGERPRINT


class MockVerifyResult:
    """
    Minimal stand-in for a python-gnupg `Verify` result, exposing only the
    attributes used to resolve the signature ID.
    """

    def __init__(self, fingerprint=None, sig_info=None, signature_id=None):
        self.fingerprint = fingerprint
        self.sig_info = sig_info or {}
        self.signature_id = signature_id


def mock_recv_keys(self, keyserver, *keyids):
    class ImportResult:
        count = 1
        fingerprints = [TEST_SEARCH_FINGERPRINT]

    self.import_keys(TEST_RECEIVE_KEY)

    return ImportResult()
