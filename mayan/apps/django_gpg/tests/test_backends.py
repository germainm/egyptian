from mayan.apps.testing.tests.base import BaseTestCase

from ..backends.python_gnupg import PythonGNUPGBackend

from .literals import (
    TEST_KEY_PRIVATE_FINGERPRINT, TEST_SEARCH_FINGERPRINT,
    TEST_SIGNATURE_ID, TEST_SIGNATURE_ID_ALTERNATE
)
from .mocks import MockVerifyResult


class PythonGNUPGBackendSignatureIDTestCase(BaseTestCase):
    def test_signature_id_from_attribute(self):
        verify_result = MockVerifyResult(
            fingerprint=TEST_KEY_PRIVATE_FINGERPRINT,
            signature_id=TEST_SIGNATURE_ID
        )

        self.assertEqual(
            PythonGNUPGBackend._get_verify_result_signature_id(
                verify_result=verify_result
            ), TEST_SIGNATURE_ID
        )

    def test_signature_id_from_sig_info_fingerprint_match(self):
        verify_result = MockVerifyResult(
            fingerprint=TEST_KEY_PRIVATE_FINGERPRINT, sig_info={
                TEST_SIGNATURE_ID_ALTERNATE: {
                    'fingerprint': TEST_SEARCH_FINGERPRINT
                },
                TEST_SIGNATURE_ID: {
                    'fingerprint': TEST_KEY_PRIVATE_FINGERPRINT
                }
            }
        )

        self.assertEqual(
            PythonGNUPGBackend._get_verify_result_signature_id(
                verify_result=verify_result
            ), TEST_SIGNATURE_ID
        )

    def test_signature_id_from_sig_info_fallback(self):
        verify_result = MockVerifyResult(
            sig_info={
                TEST_SIGNATURE_ID: {
                    'fingerprint': TEST_KEY_PRIVATE_FINGERPRINT
                }
            }
        )

        self.assertEqual(
            PythonGNUPGBackend._get_verify_result_signature_id(
                verify_result=verify_result
            ), TEST_SIGNATURE_ID
        )

    def test_signature_id_without_sig_info(self):
        verify_result = MockVerifyResult(
            fingerprint=TEST_KEY_PRIVATE_FINGERPRINT
        )

        self.assertIsNone(
            PythonGNUPGBackend._get_verify_result_signature_id(
                verify_result=verify_result
            )
        )
