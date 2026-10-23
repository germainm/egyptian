import logging
import os
from shutil import copyfileobj
import subprocess

from django.apps import apps
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.classes import ConverterBase
from mayan.apps.converter.literals import CONVERTER_OFFICE_FILE_MIMETYPES
from mayan.apps.storage.utils import NamedTemporaryFile

from .exceptions import ParserError
from .settings import setting_pdftotext_path, setting_pdftotext_timeout

logger = logging.getLogger(name=__name__)


class Parser:
    _registry = {}

    @classmethod
    def parse_document_file_page(cls, document_file_page):
        parser_classes = cls._registry.get(
            document_file_page.document_file.mimetype, ()
        )

        for parser_class in parser_classes:
            try:
                parser = parser_class()
                parser.process_document_file_page(
                    document_file_page=document_file_page
                )
            except ParserError:
                """If parser raises error, try next parser in the list."""
            else:
                return

    @classmethod
    def parse_document_file(cls, document_file):
        parser_classes = cls._registry.get(
            document_file.mimetype, ()
        )

        for parser_class in parser_classes:
            try:
                parser = parser_class()
                parser.process_document_file(document_file)
            except ParserError:
                """If parser raises error, try next parser in the list."""
            else:
                return

    @classmethod
    def register(cls, mimetypes, parser_classes):
        for mimetype in mimetypes:
            for parser_class in parser_classes:
                cls._registry.setdefault(
                    mimetype, []
                ).append(parser_class)

    def process_document_file(self, document_file):
        logger.debug(
            'Starting parsing for document file: %s', document_file
        )
        logger.debug('document file: %d', document_file.pk)

        for document_file_page in document_file.pages.all():
            self.process_document_file_page(
                document_file_page=document_file_page
            )

    def process_document_file_page(self, document_file_page):
        DocumentFilePageContent = apps.get_model(
            app_label='document_parsing',
            model_name='DocumentFilePageContent'
        )

        logger.debug(
            'Processing page: %d of document file: %s',
            document_file_page.page_number, document_file_page.document_file
        )

        with document_file_page.document_file.open() as file_object:
            try:
                parsed_content = self.execute(
                    file_object=file_object,
                    page_number=document_file_page.page_number
                )

                DocumentFilePageContent.objects.update_or_create(
                    document_file_page=document_file_page, defaults={
                        'content': parsed_content
                    }
                )

            except Exception as exception:
                error_message = _(message='Exception parsing page; %s') % exception
                logger.error(error_message, exc_info=True)
                raise ParserError(error_message)
            finally:
                file_object.close()

        logger.debug(
            'Finished processing page: %d of document file: %s',
            document_file_page.page_number, document_file_page.document_file
        )

    def execute(self, file_object, page_number):
        raise NotImplementedError(
            'Your %s class has not defined the required execute() method.' %
            self.__class__.__name__
        )


class PopplerParser(Parser):
    def __init__(self):
        self.pdftotext_path = setting_pdftotext_path.value
        if not os.path.exists(self.pdftotext_path):
            error_message = _(
                message='Cannot find pdftotext executable at: %s'
            ) % self.pdftotext_path
            logger.error(error_message)
            raise ParserError(error_message)

        logger.debug('self.pdftotext_path: %s', self.pdftotext_path)

    def execute(self, file_object, page_number):
        logger.debug('Parsing PDF page: %d', page_number)

        with NamedTemporaryFile() as temporary_file_object:
            copyfileobj(fsrc=file_object, fdst=temporary_file_object)
            temporary_file_object.seek(0)

            command = []
            command.append(self.pdftotext_path)
            command.append('-f')
            command.append(
                str(page_number)
            )
            command.append('-l')
            command.append(
                str(page_number)
            )
            command.append(temporary_file_object.name)
            command.append('-')

            timeout = setting_pdftotext_timeout.value

            with subprocess.Popen(
                command, close_fds=True, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            ) as process:
                try:
                    output, error_output = process.communicate(
                        timeout=timeout
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()

                    error_message = _(
                        message='pdftotext did not finish parsing page '
                        '%(page_number)d after %(timeout)d seconds and was '
                        'terminated.'
                    ) % {'page_number': page_number, 'timeout': timeout}
                    logger.error(error_message)

                    raise ParserError(error_message)

                return_code = process.returncode

            if return_code != 0:
                logger.error(error_output)

                raise ParserError

            if output == b'\x0c':
                logger.debug('Parser didn\'t return any output')
                return ''

            if output[-3:] == b'\x0a\x0a\x0c':
                return force_str(
                    s=output[:-3]
                )

            return force_str(s=output)


class OfficePopplerParser(PopplerParser):
    def execute(self, file_object, page_number):
        converter = ConverterBase.get_converter_class()(
            file_object=file_object
        )
        with converter.to_pdf() as pdf_file_object:
            return super().execute(
                file_object=pdf_file_object, page_number=page_number
            )


Parser.register(
    mimetypes=('application/pdf',),
    parser_classes=(PopplerParser,)
)
Parser.register(
    mimetypes=CONVERTER_OFFICE_FILE_MIMETYPES,
    parser_classes=(OfficePopplerParser,)
)
