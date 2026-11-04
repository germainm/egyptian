"""
Text of the emails, read from the PDF file that gives the images of their
pages.
"""
from email.message import EmailMessage
import importlib.util
import io
import shutil
import unittest
from unittest import mock

from django.test import SimpleTestCase

from mayan.apps.converter.backends.python import Python
from mayan.apps.converter.classes import ConverterBase
from mayan.apps.storage.tests.test_outlook import (
    make_message, text, unicode_stream
)

from ..exceptions import ParserError
from ..parsers import EmailParser, OfficePopplerParser, Parser

READY = bool(
    importlib.util.find_spec('weasyprint') and shutil.which('pdftotext')
)


def make_email(body='Corps du message.'):
    message = EmailMessage()
    message['From'] = 'Alice <alice@example.com>'
    message['To'] = 'bob@example.com'
    message['Subject'] = 'Facture été 2026'
    message.set_content(body)
    message.add_attachment(
        b'x' * 2048, maintype='application', subtype='pdf',
        filename='facture.pdf'
    )
    return message.as_bytes()


class RegistryTestCase(SimpleTestCase):
    def test_emails_have_a_parser(self):
        self.assertIn(EmailParser, Parser._registry['message/rfc822'])

    def test_outlook_messages_have_a_parser(self):
        self.assertIn(
            OfficePopplerParser,
            Parser._registry['application/vnd.ms-outlook']
        )

    def test_registered_once(self):
        self.assertEqual(
            Parser._registry['application/vnd.ms-office'].count(
                OfficePopplerParser
            ), 1
        )


@unittest.skipUnless(READY, 'WeasyPrint or pdftotext not installed')
@unittest.skipUnless(READY, 'WeasyPrint or pdftotext not installed')
class OutlookMessageParserTestCase(SimpleTestCase):
    def test_each_page_has_its_text_and_one_rendering(self):
        message = make_message(
            **{
                unicode_stream(0x1000): text(
                    '\n'.join('Ligne {}'.format(index) for index in range(150))
                )
            }
        )
        data = message.getvalue()
        with mock.patch.object(
            ConverterBase, 'get_converter_class', wraps=ConverterBase.get_converter_class
        ) as mocked:
            parser = OfficePopplerParser()
            parser.mime_type = 'application/vnd.ms-outlook'
            first = parser.execute(file_object=io.BytesIO(data), page_number=1)
            second = parser.execute(file_object=io.BytesIO(data), page_number=2)

        self.assertEqual(mocked.call_count, 1)
        self.assertIn('alice@example.com', first)
        self.assertIn('Ligne 0', first)
        self.assertNotIn('alice@example.com', second)
        self.assertIn('Ligne 40', second)

    def test_parser_detects_the_type_of_the_file(self):
        converter = mock.MagicMock()
        converter.return_value.to_pdf.side_effect = OSError('arrêt')
        with mock.patch.object(
            ConverterBase, 'get_converter_class', return_value=converter
        ):
            with self.assertRaises(OSError):
                OfficePopplerParser().execute(
                    file_object=io.BytesIO(b'x'), page_number=1
                )
        self.assertIsNone(converter.call_args.kwargs['mime_type'])

        # An email is rendered as one, whatever its content looks like.
        with mock.patch.object(
            ConverterBase, 'get_converter_class', return_value=converter
        ):
            with self.assertRaises(OSError):
                EmailParser().execute(
                    file_object=io.BytesIO(b'x'), page_number=1
                )
        self.assertEqual(
            converter.call_args.kwargs['mime_type'], 'message/rfc822'
        )


class EmailParserTestCase(SimpleTestCase):
    def test_headers_body_and_attachments(self):
        text = EmailParser().execute(
            file_object=io.BytesIO(make_email()), page_number=1
        )
        for expected in (
            'alice@example.com', 'bob@example.com', 'Facture été 2026',
            'Corps du message.', 'facture.pdf'
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_attachment_content_not_read(self):
        text = EmailParser().execute(
            file_object=io.BytesIO(make_email()), page_number=1
        )
        self.assertNotIn('xxxx', text)

    def test_html_body_without_markup(self):
        email = (
            'From: a@example.com\r\nSubject: Essai\r\nMIME-Version: 1.0\r\n'
            'Content-Type: text/html; charset=utf-8\r\n\r\n'
            '<p>Un <b>mot</b> important</p>'
        ).encode()
        text = EmailParser().execute(
            file_object=io.BytesIO(email), page_number=1
        )
        self.assertIn('Un mot important', text)
        self.assertNotIn('<b>', text)

    def test_each_page_has_its_text_and_one_rendering(self):
        email = make_email(
            body='\n'.join('Ligne {}.'.format(index) for index in range(400))
        )
        parser = EmailParser()
        with mock.patch.object(
            Python, '_eml_to_pdf_bytes', autospec=True,
            side_effect=Python._eml_to_pdf_bytes
        ) as renderer:
            first = parser.execute(file_object=io.BytesIO(email), page_number=1)
            second = parser.execute(file_object=io.BytesIO(email), page_number=2)

        self.assertEqual(renderer.call_count, 1)
        self.assertIn('Ligne 0.', first)
        self.assertNotIn('Ligne 0.', second)
        self.assertIn('Ligne', second)

    def test_rendering_error_is_a_parser_error(self):
        document_file_page = mock.MagicMock()
        document_file_page.document_file.open.return_value.__enter__.return_value = io.BytesIO(b'')
        with mock.patch.object(
            Python, '_eml_to_pdf_bytes',
            side_effect=ValueError('rendu impossible')
        ):
            with self.assertRaises(ParserError):
                EmailParser().process_document_file_page(
                    document_file_page=document_file_page
                )

