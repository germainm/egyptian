import logging
import shlex

import sh

from django.utils.translation import gettext_lazy as _

from mayan.apps.file_metadata.classes import FileMetadataDriver

from .literals import (
    DEFAULT_CLAMSCAN_ARGUMENTS, DEFAULT_PATH_CLAMSCAN,
    DEFAULT_TIMEOUT_CLAMSCAN, SCAN_SUMMARY_MARKER
)

__all__ = ('ClamScanDriver', 'ClamScanRawFileDriver')
logger = logging.getLogger(name=__name__)


class ClamScanDriverMixin:
    argument_name_list = (
        'arguments_clamscan', 'path_clamscan', 'timeout_clamscan'
    )
    mime_type_list = ('*',)

    _raw = False

    @classmethod
    def get_argument_values_from_settings(cls):
        result = {
            'arguments_clamscan': DEFAULT_CLAMSCAN_ARGUMENTS,
            'path_clamscan': DEFAULT_PATH_CLAMSCAN,
            'timeout_clamscan': DEFAULT_TIMEOUT_CLAMSCAN
        }

        setting_arguments = super().get_argument_values_from_settings()

        if setting_arguments:
            result.update(setting_arguments)

        return result

    def __init__(
        self, path_clamscan, arguments_clamscan=None, timeout_clamscan=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if timeout_clamscan is None:
            timeout_clamscan = DEFAULT_TIMEOUT_CLAMSCAN

        self.timeout_clamscan = int(timeout_clamscan)

        argument_list = self._get_argument_list(
            arguments_clamscan=arguments_clamscan
        )

        try:
            command_clamscan = sh.Command(path=path_clamscan)
        except sh.CommandNotFound:
            logger.error(
                'clamscan binary not found at: %s', path_clamscan
            )
            self.command_clamscan = None
        else:
            self.command_clamscan = command_clamscan.bake(*argument_list)

    def _get_argument_list(self, arguments_clamscan):
        if arguments_clamscan is None:
            arguments_clamscan = DEFAULT_CLAMSCAN_ARGUMENTS

        if isinstance(arguments_clamscan, str):
            result = shlex.split(s=arguments_clamscan)
        else:
            result = list(arguments_clamscan)

        return result

    def _get_scan_result(self, path_document_file):
        output = self.command_clamscan(
            path_document_file, _ok_code=(0, 1),
            _timeout=self.timeout_clamscan
        )
        result = {}
        start_of_data = False

        for line in output.split('\n'):
            if start_of_data:
                parts = line.split(':', 1)

                if len(parts) > 1:
                    key = parts[0]
                    value = parts[1]
                    value = value.strip()
                    result[key] = value

            if SCAN_SUMMARY_MARKER in line:
                start_of_data = True

        return result

    def _process(self, document_file):
        if self.command_clamscan:
            with self.get_document_file_path(
                document_file=document_file, raw=self._raw
            ) as path_document_file:
                return self._get_scan_result(
                    path_document_file=path_document_file
                )
        else:
            logger.error(
                'clamscan binary not found, not processing document '
                'file: %s', document_file
            )


class ClamScanDriver(ClamScanDriverMixin, FileMetadataDriver):
    description = _(
        message='Command line anti-virus scanner. Scans the content of a '
        'document file, after it was decoded. This is the scan that detects '
        'malware carried inside a document file that was submitted wrapped, '
        'in an OpenPGP container for example.'
    )
    enabled = False
    internal_name = 'clamscan'
    label = _(message='ClamScan')


class ClamScanRawFileDriver(ClamScanDriverMixin, FileMetadataDriver):
    _raw = True

    description = _(
        message='Command line anti-virus scanner. Scans a document file as '
        'it was submitted, before it is decoded. Meant to be enabled in '
        'addition to the ClamScan driver and not instead of it: an '
        'anti-virus scan of a wrapped document file, an OpenPGP '
        'container for example, does not match the content it carries, '
        'only the ClamScan driver detects that. Adds coverage only when a '
        'pre open hook transforms the document file, such as when using '
        'embedded signatures. Otherwise it scans the same bytes as the '
        'ClamScan driver.'
    )
    enabled = False
    internal_name = 'clamscan_raw'
    label = _(message='ClamScan (raw file)')
