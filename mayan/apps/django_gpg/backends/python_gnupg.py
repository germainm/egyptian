import logging

import gnupg

from mayan.apps.storage.utils import TemporaryDirectory

from ..classes import GPGBackend
from ..literals import DEFAULT_GPG_PATH
from ..settings import setting_gpg_backend_arguments

gpg_path = setting_gpg_backend_arguments.value.get(
    'gpg_path', DEFAULT_GPG_PATH
)
logger = logging.getLogger(name=__name__)


class PythonGNUPGBackend(GPGBackend):
    @staticmethod
    def _decrypt_file(gpg, file_object, keys):
        for key in keys:
            gpg.import_keys(
                key_data=key['key_data']
            )

        return gpg.decrypt_file(fileobj_or_path=file_object)

    @staticmethod
    def _get_verify_result_signature_id(verify_result):
        if verify_result.signature_id:
            return verify_result.signature_id

        fingerprint = verify_result.fingerprint
        signature_information = verify_result.sig_info or {}

        for signature_id, entry in signature_information.items():
            if fingerprint and entry.get('fingerprint') == fingerprint:
                return signature_id

        # No fingerprint match was found. Fall back to the first entry
        # available, if any.
        for signature_id in signature_information:
            return signature_id

        return None

    @staticmethod
    def _import_and_list_keys(gpg, **kwargs):
        import_results = gpg.import_keys(**kwargs)
        return import_results, gpg.list_keys(
            keys=import_results.fingerprints[0]
        )[0]

    @staticmethod
    def _import_key(gpg, **kwargs):
        return gpg.import_keys(**kwargs)

    @staticmethod
    def _list_keys(gpg, **kwargs):
        return gpg.list_keys(**kwargs)

    @staticmethod
    def _recv_keys(gpg, keyserver, key_id):
        import_results = gpg.recv_keys(keyserver, key_id)
        if import_results.count:
            key_data = gpg.export_keys(
                import_results.fingerprints[0]
            )
        else:
            key_data = None
        return key_data

    @staticmethod
    def _search_keys(gpg, keyserver, query):
        return gpg.search_keys(keyserver=keyserver, query=query)

    @staticmethod
    def _sign_file(
        binary, clearsign, detached, file_object, gpg, key_data, output,
        passphrase
    ):
        import_results = gpg.import_keys(key_data=key_data)

        return gpg.sign_file(
            binary=binary, clearsign=clearsign, detach=detached,
            fileobj_or_path=file_object, keyid=import_results.fingerprints[0],
            output=output, passphrase=passphrase
        )

    @staticmethod
    def _verify_file(gpg, file_object, keys, data_filename=None):
        for key in keys:
            gpg.import_keys(
                key_data=key['key_data']
            )

        verify_result = gpg.verify_file(
            fileobj_or_path=file_object, data_filename=data_filename
        )

        verify_result.signature_id = PythonGNUPGBackend._get_verify_result_signature_id(
            verify_result=verify_result
        )

        return verify_result

    def decrypt_file(self, file_object, keys):
        return self.gpg_command(
            file_object=file_object,
            function=PythonGNUPGBackend._decrypt_file, keys=keys
        )

    def gpg_command(self, function, **kwargs):
        with TemporaryDirectory() as temporary_directory:
            gpg = gnupg.GPG(
                gpgbinary=self.kwargs['gpg_path'],
                gnupghome=temporary_directory
            )
            return function(gpg=gpg, **kwargs)

    def import_and_list_keys(self, key_data):
        return self.gpg_command(
            function=PythonGNUPGBackend._import_and_list_keys,
            key_data=key_data
        )

    def import_key(self, key_data):
        return self.gpg_command(
            function=PythonGNUPGBackend._import_key, key_data=key_data
        )

    def list_keys(self, keys):
        return self.gpg_command(
            function=PythonGNUPGBackend._list_keys, keys=keys
        )

    def recv_keys(self, keyserver, key_id):
        return self.gpg_command(
            function=PythonGNUPGBackend._recv_keys, key_id=key_id,
            keyserver=keyserver
        )

    def search_keys(self, keyserver, query):
        return self.gpg_command(
            function=PythonGNUPGBackend._search_keys, keyserver=keyserver,
            query=query
        )

    def sign_file(
        self, binary, clearsign, detached, file_object, key_data, output,
        passphrase
    ):
        return self.gpg_command(
            binary=binary, clearsign=clearsign, detached=detached,
            file_object=file_object, function=PythonGNUPGBackend._sign_file,
            key_data=key_data, output=output, passphrase=passphrase
        )

    def verify_file(self, file_object, keys, data_filename=None):
        return self.gpg_command(
            data_filename=data_filename, file_object=file_object,
            function=PythonGNUPGBackend._verify_file, keys=keys
        )
