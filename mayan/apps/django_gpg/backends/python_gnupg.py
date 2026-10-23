import logging
import shutil
import subprocess
from urllib.parse import unquote

from mayan.apps.storage.utils import NamedTemporaryFile, TemporaryDirectory

from ..classes import GPGBackend
from ..exceptions import GPGException
from ..literals import (
    DEFAULT_GPG_KEYSERVER_TIMEOUT, DEFAULT_GPG_PATH, DEFAULT_GPG_TIMEOUT
)
from ..settings import setting_gpg_backend_arguments

gpg_path = setting_gpg_backend_arguments.value.get(
    'gpg_path', DEFAULT_GPG_PATH
)
logger = logging.getLogger(name=__name__)

STATUS_PREFIX = '[GNUPG:] '
STATUS_PREFIX_LENGTH = len(STATUS_PREFIX)

IMPORT_OK_SECRET_KEY = 16

TRUST_LEVELS = {
    'TRUST_EXPIRED': 0,
    'TRUST_UNDEFINED': 1,
    'TRUST_NEVER': 2,
    'TRUST_MARGINAL': 3,
    'TRUST_FULLY': 4,
    'TRUST_ULTIMATE': 5
}


class GPGResult:
    def __init__(self, returncode=0, status_lines=None, stderr=''):
        self.returncode = returncode
        self.status_lines = status_lines or []
        self.stderr = stderr


class ImportResult(GPGResult):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fingerprints = []
        self.key_count = 0
        self.secret_key_imported = False


class SignResult(GPGResult):
    def __init__(
        self, data=b'', passphrase_bad=False, passphrase_needed=False,
        signature_created=False, **kwargs
    ):
        super().__init__(**kwargs)
        self.data = data
        self.passphrase_bad = passphrase_bad
        self.passphrase_needed = passphrase_needed
        self.signature_created = signature_created

    def __bool__(self):
        return bool(self.data)

    def __bytes__(self):
        return self.data

    def __str__(self):
        return self.data.decode(encoding='utf-8', errors='replace')


class DecryptResult(GPGResult):
    def __init__(self, data=b'', success=False, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.success = success

    def __bool__(self):
        return self.success


class VerifyResult(GPGResult):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.expire_timestamp = None
        self.fingerprint = None
        self.key_id = None
        self.key_missing = False
        self.pubkey_fingerprint = None
        self.signature_id = None
        self.signature_present = False
        self.timestamp = None
        self.trust_level = None
        self.trust_text = None
        self.username = None
        self.valid = False

    def __bool__(self):
        return self.valid


class PythonGNUPGBackend(GPGBackend):
    @staticmethod
    def _build_verify_result(gpg_result):
        verify_result = VerifyResult(
            returncode=gpg_result.returncode,
            status_lines=gpg_result.status_lines, stderr=gpg_result.stderr
        )

        for keyword, value in gpg_result.status_lines:
            fields = value.split()

            if keyword == 'NEWSIG':
                verify_result.signature_present = True
            elif keyword == 'SIG_ID':
                verify_result.signature_present = True
                verify_result.signature_id = fields[0]
                if len(fields) >= 3:
                    verify_result.timestamp = fields[2]
            elif keyword in ('GOODSIG', 'EXPSIG', 'EXPKEYSIG', 'REVKEYSIG'):
                verify_result.signature_present = True
                verify_result.key_id = fields[0]
                if len(fields) >= 2:
                    verify_result.username = value.split(None, 1)[1]
            elif keyword == 'BADSIG':
                verify_result.signature_present = True
                verify_result.key_id = fields[0]
                if len(fields) >= 2:
                    verify_result.username = value.split(None, 1)[1]
            elif keyword == 'VALIDSIG':
                verify_result.signature_present = True
                verify_result.valid = True
                verify_result.fingerprint = fields[0]
                if len(fields) >= 4:
                    verify_result.timestamp = fields[2]
                    expire_timestamp = fields[3]
                    verify_result.expire_timestamp = (
                        None if expire_timestamp == '0' else expire_timestamp
                    )
                if len(fields) >= 10:
                    verify_result.pubkey_fingerprint = fields[9]
                else:
                    verify_result.pubkey_fingerprint = fields[0]
            elif keyword == 'ERRSIG':
                verify_result.signature_present = True
                verify_result.key_id = fields[0]
                verify_result.key_missing = True
                if len(fields) >= 5:
                    verify_result.timestamp = fields[4]
            elif keyword == 'NO_PUBKEY':
                verify_result.signature_present = True
                verify_result.key_id = fields[0]
                verify_result.key_missing = True
            elif keyword in TRUST_LEVELS:
                verify_result.trust_text = keyword
                verify_result.trust_level = TRUST_LEVELS[keyword]

        return verify_result

    def _get_timeout(self, keyserver=False):
        if keyserver:
            return self.kwargs.get(
                'timeout_keyserver', DEFAULT_GPG_KEYSERVER_TIMEOUT
            )
        else:
            return self.kwargs.get('timeout', DEFAULT_GPG_TIMEOUT)

    def _execute(
        self, arguments, gpg_home, input_path=None, output_stream=None,
        timeout=None
    ):
        if timeout is None:
            timeout = self._get_timeout()

        command = [
            self.kwargs['gpg_path'], '--batch', '--no-tty', '--yes',
            '--homedir', gpg_home, '--pinentry-mode', 'loopback',
            '--status-fd', '2'
        ]

        command.extend(arguments)

        if input_path is not None:
            command.append(input_path)

        logger.debug('gpg command: %s', command)

        if output_stream is None:
            stdout = subprocess.DEVNULL
        else:
            stdout = output_stream

        with NamedTemporaryFile() as stderr_file:
            try:
                process = subprocess.run(
                    args=command, check=False, stderr=stderr_file,
                    stdin=subprocess.DEVNULL, stdout=stdout, timeout=timeout
                )
            except subprocess.TimeoutExpired:
                error_message = 'gpg did not finish after {} seconds and was terminated.'.format(
                    timeout
                )
                logger.error(error_message)

                raise GPGException(error_message)

            stderr_file.seek(0)
            raw_stderr = stderr_file.read()
            stderr = raw_stderr.decode(
                encoding='utf-8', errors='replace'
            )

        status_lines = []
        for line in stderr.splitlines():
            if line.startswith(STATUS_PREFIX):
                keyword, separator, value = line[STATUS_PREFIX_LENGTH:].partition(' ')
                status_lines.append(
                    (keyword, value)
                )

        return GPGResult(
            returncode=process.returncode, status_lines=status_lines,
            stderr=stderr
        )

    def _import_key(self, gpg_home, key_data):
        if isinstance(key_data, str):
            key_data = key_data.encode('utf-8')

        with NamedTemporaryFile() as key_file:
            key_file.write(key_data)
            key_file.flush()

            gpg_result = self._execute(
                arguments=['--import'], gpg_home=gpg_home,
                input_path=key_file.name
            )

        import_result = ImportResult(
            returncode=gpg_result.returncode,
            status_lines=gpg_result.status_lines, stderr=gpg_result.stderr
        )

        for keyword, value in gpg_result.status_lines:
            if keyword == 'IMPORT_OK':
                reason, separator, fingerprint = value.partition(' ')
                fingerprint = fingerprint.strip()
                if fingerprint:
                    import_result.fingerprints.append(fingerprint)
                try:
                    secret_key = int(reason) & IMPORT_OK_SECRET_KEY
                except ValueError:
                    secret_key = False
                if secret_key:
                    import_result.secret_key_imported = True
            elif keyword == 'IMPORT_RES':
                fields = value.split()
                if fields:
                    try:
                        import_result.key_count = int(
                            fields[0]
                        )
                    except ValueError:
                        import_result.key_count = 0

        if not import_result.key_count:
            import_result.key_count = len(import_result.fingerprints)

        return import_result

    def _list_keys(self, gpg_home, keys=None):
        arguments = [
            '--list-keys', '--fixed-list-mode', '--with-colons',
            '--with-fingerprint'
        ]
        if keys:
            if isinstance(keys, (list, tuple)):
                arguments.extend(keys)
            else:
                arguments.append(keys)

        with NamedTemporaryFile() as output_file:
            self._execute(
                arguments=arguments, gpg_home=gpg_home,
                output_stream=output_file
            )
            output_file.seek(0)
            listing = output_file.read().decode(
                encoding='utf-8', errors='replace'
            )

        return self._parse_key_listing(listing=listing)

    @staticmethod
    def _parse_key_listing(listing):
        keys = []
        current_key = None

        for line in listing.splitlines():
            fields = line.split(':')
            record_type = fields[0]

            if record_type in ('pub', 'sec') and len(fields) >= 7:
                current_key = {
                    'algo': fields[3], 'date': fields[5],
                    'expires': fields[6], 'fingerprint': None,
                    'keyid': fields[4], 'length': fields[2],
                    'type': record_type, 'uids': []
                }
                keys.append(current_key)
            elif record_type == 'fpr' and current_key is not None:
                if current_key['fingerprint'] is None and len(fields) >= 10:
                    current_key['fingerprint'] = fields[9]
            elif record_type == 'uid' and current_key is not None:
                if len(fields) >= 10 and fields[9]:
                    current_key['uids'].append(
                        fields[9]
                    )

        return keys

    @staticmethod
    def _parse_search_listing(listing):
        keys = []
        current_key = None

        for line in listing.splitlines():
            fields = line.split(':')
            record_type = fields[0]

            if record_type == 'pub' and len(fields) >= 6:
                current_key = {
                    'algo': fields[2], 'date': fields[4],
                    'expires': fields[5], 'keyid': fields[1],
                    'length': fields[3], 'type': 'pub', 'uids': []
                }
                keys.append(current_key)
            elif record_type == 'uid' and current_key is not None:
                if len(fields) >= 2 and fields[1]:
                    unquoted_uid = unquote(
                        string=fields[1]
                    )
                    current_key['uids'].append(unquoted_uid)

        return keys

    def decrypt_file(self, file_object, keys):
        with TemporaryDirectory() as gpg_home:
            for key in keys:
                self._import_key(
                    gpg_home=gpg_home, key_data=key['key_data']
                )

            with NamedTemporaryFile() as input_file:
                shutil.copyfileobj(fdst=input_file, fsrc=file_object)
                input_file.flush()

                with NamedTemporaryFile() as output_file:
                    gpg_result = self._execute(
                        arguments=['--decrypt', '--output', output_file.name],
                        gpg_home=gpg_home, input_path=input_file.name
                    )
                    output_file.seek(0)
                    data = output_file.read()

        decrypt_result = DecryptResult(
            data=data, returncode=gpg_result.returncode,
            status_lines=gpg_result.status_lines, stderr=gpg_result.stderr
        )

        keywords = [keyword for keyword, value in gpg_result.status_lines]
        decrypt_result.success = bool(data) and 'NODATA' not in keywords

        return decrypt_result

    def import_and_list_keys(self, key_data):
        with TemporaryDirectory() as gpg_home:
            import_result = self._import_key(
                gpg_home=gpg_home, key_data=key_data
            )
            key_list = self._list_keys(
                gpg_home=gpg_home, keys=import_result.fingerprints[0]
            )
            return import_result, key_list[0]

    def import_key(self, key_data):
        with TemporaryDirectory() as gpg_home:
            return self._import_key(gpg_home=gpg_home, key_data=key_data)

    def list_keys(self, keys):
        with TemporaryDirectory() as gpg_home:
            return self._list_keys(gpg_home=gpg_home, keys=keys)

    def recv_keys(self, keyserver, key_id):
        with TemporaryDirectory() as gpg_home:
            import_result = ImportResult()
            gpg_result = self._execute(
                arguments=['--keyserver', keyserver, '--recv-keys', key_id],
                gpg_home=gpg_home, timeout=self._get_timeout(keyserver=True)
            )
            for keyword, value in gpg_result.status_lines:
                if keyword == 'IMPORT_OK':
                    reason, separator, fingerprint = value.partition(' ')
                    fingerprint = fingerprint.strip()
                    if fingerprint:
                        import_result.fingerprints.append(fingerprint)

            if not import_result.fingerprints:
                return None

            with NamedTemporaryFile() as output_file:
                self._execute(
                    arguments=[
                        '--armor', '--export', '--output', output_file.name,
                        import_result.fingerprints[0]
                    ], gpg_home=gpg_home
                )
                output_file.seek(0)
                return output_file.read().decode(
                    encoding='utf-8', errors='replace'
                )

    def search_keys(self, keyserver, query):
        with TemporaryDirectory() as gpg_home:
            with NamedTemporaryFile() as output_file:
                self._execute(
                    arguments=[
                        '--keyserver', keyserver, '--with-colons',
                        '--search-keys', query
                    ], gpg_home=gpg_home, output_stream=output_file,
                    timeout=self._get_timeout(keyserver=True)
                )
                output_file.seek(0)
                listing = output_file.read().decode(
                    encoding='utf-8', errors='replace'
                )

        return self._parse_search_listing(listing=listing)

    def sign_file(
        self, file_object, key_data, binary=False, clearsign=False,
        detached=False, output=None, passphrase=None
    ):
        with TemporaryDirectory() as gpg_home:
            import_result = self._import_key(
                gpg_home=gpg_home, key_data=key_data
            )
            fingerprint = import_result.fingerprints[0]

            arguments = ['--local-user', fingerprint]
            if not binary:
                arguments.append('--armor')

            if clearsign:
                arguments.append('--clearsign')
            elif detached:
                arguments.append('--detach-sign')
            else:
                arguments.append('--sign')

            with NamedTemporaryFile() as input_file:
                shutil.copyfileobj(fdst=input_file, fsrc=file_object)
                input_file.flush()

                with NamedTemporaryFile() as passphrase_file, \
                        NamedTemporaryFile() as output_file:
                    if passphrase is not None:
                        if isinstance(passphrase, str):
                            passphrase = passphrase.encode('utf-8')
                        passphrase_file.write(passphrase)
                        passphrase_file.flush()
                        arguments.extend(
                            ['--passphrase-file', passphrase_file.name]
                        )

                    output_path = output or output_file.name
                    arguments.extend(
                        ['--output', output_path]
                    )

                    gpg_result = self._execute(
                        arguments=arguments, gpg_home=gpg_home,
                        input_path=input_file.name
                    )

                    if output:
                        with open(file=output_path, mode='rb') as signed_file:
                            data = signed_file.read()
                    else:
                        output_file.seek(0)
                        data = output_file.read()

        sign_result = SignResult(
            data=data, returncode=gpg_result.returncode,
            status_lines=gpg_result.status_lines, stderr=gpg_result.stderr
        )

        keywords = [keyword for keyword, value in gpg_result.status_lines]
        sign_result.signature_created = 'SIG_CREATED' in keywords
        if not sign_result.signature_created:
            if 'NEED_PASSPHRASE' in keywords:
                sign_result.passphrase_needed = True
            else:
                sign_result.passphrase_bad = True

        return sign_result

    def verify_file(self, file_object, keys, data_filename=None):
        with TemporaryDirectory() as gpg_home:
            for key in keys:
                self._import_key(
                    gpg_home=gpg_home, key_data=key['key_data']
                )

            with NamedTemporaryFile() as signature_file:
                shutil.copyfileobj(fdst=signature_file, fsrc=file_object)
                signature_file.flush()

                if data_filename is None:
                    arguments = ['--verify']
                    input_path = signature_file.name
                else:
                    arguments = [
                        '--verify', signature_file.name, data_filename
                    ]
                    input_path = None

                gpg_result = self._execute(
                    arguments=arguments, gpg_home=gpg_home,
                    input_path=input_path
                )

        return self._build_verify_result(gpg_result=gpg_result)
