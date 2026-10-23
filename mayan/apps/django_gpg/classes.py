from django.utils.module_loading import import_string

from .settings import setting_gpg_backend, setting_gpg_backend_arguments
from .utils import do_timestamp_convert


class GPGBackend:
    @staticmethod
    def get_instance():
        klass = import_string(dotted_path=setting_gpg_backend.value)
        instance = klass(**setting_gpg_backend_arguments.value)
        return instance

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class KeyStub:
    def __init__(self, raw):
        self.fingerprint = raw['keyid']
        self.key_type = raw['type']

        timestamp = int(
            raw['date']
        )

        self.date = do_timestamp_convert(timestamp=timestamp)

        if raw['expires']:
            timestamp = int(
                raw['expires']
            )
            self.expires = do_timestamp_convert(timestamp=timestamp)
        else:
            self.expires = None

        self.length = raw['length']
        self.user_id = raw['uids']

    @property
    def key_id(self):
        return self.fingerprint[-8:]


class SignatureVerification:
    def __init__(self, verify_result):
        self.fingerprint = verify_result.fingerprint
        self.key_id = verify_result.key_id
        self.pubkey_fingerprint = verify_result.pubkey_fingerprint
        self.signature_id = verify_result.signature_id
        self.trust_level = verify_result.trust_level
        self.trust_text = verify_result.trust_text
        self.username = verify_result.username
        self.valid = verify_result.valid

        if verify_result.timestamp:
            timestamp = int(verify_result.timestamp)
            self.date_time = do_timestamp_convert(timestamp=timestamp)

        if verify_result.expire_timestamp:
            timestamp = int(verify_result.expire_timestamp)
            self.expires = do_timestamp_convert(timestamp=timestamp)
        else:
            self.expires = None
