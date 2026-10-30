from django.test import SimpleTestCase

from ..client_backends import ClientBackendSentry

TEST_DSN = 'https://key@sentry.example.invalid/1'


class ClientBackendSentryTestCase(SimpleTestCase):
    def test_personal_data_not_sent_by_default(self):
        options = ClientBackendSentry(dsn=TEST_DSN).setup_arguments()
        self.assertFalse(options['send_default_pii'])

    def test_personal_data_sent_when_enabled(self):
        options = ClientBackendSentry(
            dsn=TEST_DSN, send_default_pii='true'
        ).setup_arguments()
        self.assertTrue(options['send_default_pii'])
