from io import BytesIO
import logging

from django.utils.encoding import force_bytes, force_str

from .classes import GPGBackend
from .exceptions import NeedPassphrase, PassphraseError
from .literals import KEY_TYPE_SECRET
from .utils import do_timestamp_convert

logger = logging.getLogger(name=__name__)


class KeyBusinessLogicMixin:
    @property
    def key_id(self):
        return self.fingerprint[-8:]

    def introspect_key_data(self):
        self.key_data = force_str(s=self.key_data)
        backend = GPGBackend.get_instance()
        import_results, key_info = backend.import_and_list_keys(
            key_data=self.key_data
        )
        logger.debug('key_info: %s', key_info)

        self.algorithm = key_info['algo']
        timestamp = int(
            key_info['date']
        )
        self.creation_date = do_timestamp_convert(timestamp=timestamp)

        if key_info['expires']:
            timestamp = int(
                key_info['expires']
            )
            self.expiration_date = do_timestamp_convert(timestamp=timestamp)

        self.fingerprint = key_info['fingerprint']
        self.length = int(
            key_info['length']
        )
        self.user_id = key_info['uids'][0]
        if import_results.secret_key_imported:
            self.key_type = KEY_TYPE_SECRET
        else:
            self.key_type = key_info['type']

    def open(self, **kwargs):
        initial_bytes = force_bytes(s=self.key_data)
        output_buffer = BytesIO(initial_bytes=initial_bytes)
        return output_buffer

    def sign_file(
        self, file_object, binary=False, clearsign=False, detached=False,
        output=None, passphrase=None
    ):
        backend = GPGBackend.get_instance()
        file_sign_results = backend.sign_file(
            binary=binary, clearsign=clearsign, detached=detached,
            file_object=file_object, key_data=self.key_data,
            output=output, passphrase=passphrase
        )

        logger.debug(
            'file_sign_results.stderr: %s', file_sign_results.stderr
        )

        if file_sign_results.passphrase_needed:
            raise NeedPassphrase

        if file_sign_results.passphrase_bad:
            raise PassphraseError

        return file_sign_results
