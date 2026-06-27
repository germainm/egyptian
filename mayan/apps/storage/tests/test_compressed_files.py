import hashlib
import zipfile

from django.utils.encoding import force_bytes

from mayan.apps.common.tests.literals import (
    TEST_ARCHIVE_EML_SAMPLE_PATH, TEST_ARCHIVE_MSG_STRANGE_DATE_PATH,
    TEST_ARCHIVE_ZIP_CP437_MEMBER_PATH,
    TEST_ARCHIVE_ZIP_SPECIAL_CHARACTERS_FILENAME_MEMBER_PATH,
    TEST_PDF_WITH_ATTACHMENT_PATH, TEST_TAR_BZ2_FILE_PATH,
    TEST_TAR_FILE_PATH, TEST_TAR_GZ_FILE_PATH, TEST_ZIP_FILE_PATH
)
from mayan.apps.testing.tests.base import BaseTestCase

from ..compressed_files import (
    Archive, EMLArchive, MsgArchive, PDFArchive, TarArchive, ZipArchive
)
from ..exceptions import (
    ArchiveCompressionRatioExceeded, ArchiveInputSizeExceeded,
    ArchiveMemberSizeExceeded
)
from ..settings import (
    setting_compressed_file_compression_ratio_maximum,
    setting_compressed_file_input_size_maximum,
    setting_compressed_file_member_size_maximum
)

from .mixins import (
    ArchiveClassTestCaseMixin, ArchiveTarFileBuilderMixin,
    ArchiveZipFileBuilderMixin, CompressedFileSettingsResetMixin
)


class EMLArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_ARCHIVE_EML_SAMPLE_PATH
    cls = EMLArchive
    member_contents_partial = 'testtest'
    member_name = 'body'
    members_list = ['body', 'sha1hash.txt', 'manifest.json']

    def test_add_file(self):
        '''Skip this test for the class.'''

    def test_member_contents(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                archive.member_contents(
                    filename=self.member_name
                ).startswith(
                    force_bytes(s=self.member_contents_partial)
                )
            )

    def test_open_member(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            file_object = archive.open_member(filename=self.member_name)
            self.assertTrue(
                file_object.read().startswith(
                    force_bytes(s=self.member_contents_partial)
                )
            )


class MsgArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_ARCHIVE_MSG_STRANGE_DATE_PATH
    cls = MsgArchive
    member_contents_partial = '''MSG test file
Purpose: Provide example of this file type
Document file type: MSG
Version: 1.0
Remark:

Example content:
The names "John Doe" for males, "Jane Doe" or "Jane Roe" for females,
or "Jonnie Doe" and "Janie Doe" for children, or just "Doe"
non-gender-specifically are used as placeholder names for a party whose
true identity is unknown or must be withheld in a legal action, case, or
discussion. The names are also used to refer to acorpse or hospital
patient whose identity is unknown. This practice is widely used in the
United States and Canada, but is rarely used in other English-speaking
countries including the United Kingdom itself, from where the use of
"John Doe" in a legal context originates. The names Joe Bloggs or John
Smith are used in the UK instead, as well as in Australia and New
Zealand. '''.replace('\n', '\r\n')
    member_name = 'message.txt'
    members_list = ['message.txt']

    def test_add_file(self):
        '''Skip this test for the class.'''

    def test_member_contents(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                archive.member_contents(
                    filename=self.member_name
                ).startswith(
                    force_bytes(s=self.member_contents_partial)
                )
            )

    def test_open_member(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            file_object = archive.open_member(filename=self.member_name)
            self.assertTrue(
                file_object.read().startswith(
                    force_bytes(s=self.member_contents_partial)
                )
            )


class PDFArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_PDF_WITH_ATTACHMENT_PATH
    cls = PDFArchive
    member_name = '0-image.png'
    members_list = ['0-image.png']

    def test_add_file(self):
        '''Skip this test for the class.'''

    def test_member_contents(self):
        '''Override to avoid having to include the attachment file.'''

        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            member_content = archive.member_contents(
                filename=self.member_name
            )

            content_collapsed = list(member_content)
            self.assertEqual(
                len(content_collapsed), 6669
            )

    def test_open_member(self):
        '''Override to avoid having to include the attachment file.'''

        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            file_object = archive.open_member(filename=self.member_name)

            self.assertEqual(
                file_object.size, 6669
            )


class ZipArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_ZIP_FILE_PATH
    cls = ZipArchive

    def test_open_member_with_special_characters_filename(self):
        with open(file=TEST_ARCHIVE_ZIP_SPECIAL_CHARACTERS_FILENAME_MEMBER_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            list(
                archive.get_members()
            )

    def test_open_cp437_member(self):
        with open(file=TEST_ARCHIVE_ZIP_CP437_MEMBER_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            list(
                archive.get_members()
            )


class TarArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_TAR_FILE_PATH
    cls = TarArchive


class TarGzArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_TAR_GZ_FILE_PATH
    cls = TarArchive


class TarBz2ArchiveClassTestCase(ArchiveClassTestCaseMixin, BaseTestCase):
    archive_path = TEST_TAR_BZ2_FILE_PATH
    cls = TarArchive


# Memory-exhaustion defense tests.


class TarArchiveMemberSizeLimitTestCase(
    ArchiveTarFileBuilderMixin, CompressedFileSettingsResetMixin, BaseTestCase
):
    def test_member_contents_exceeds_size_maximum(self):
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        buffer = self._build_tar_archive(
            members=[('a.txt', b'X' * 16)]
        )
        archive = TarArchive()
        archive._open(file_object=buffer)

        with self.assertRaises(
            expected_exception=ArchiveMemberSizeExceeded
        ):
            archive.member_contents(filename='a.txt')

    def test_open_member_exceeds_size_maximum(self):
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        buffer = self._build_tar_archive(
            members=[('a.txt', b'X' * 16)]
        )
        archive = TarArchive()
        archive._open(file_object=buffer)

        with self.assertRaises(
            expected_exception=ArchiveMemberSizeExceeded
        ):
            archive.open_member(filename='a.txt')

    def test_legitimate_member_passes(self):
        buffer = self._build_tar_archive(
            members=[('a.txt', b'X' * 16)]
        )
        archive = TarArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='a.txt'), b'X' * 16
        )


class ZipArchiveMemberSizeLimitTestCase(
    ArchiveZipFileBuilderMixin, CompressedFileSettingsResetMixin, BaseTestCase
):
    def test_legitimate_archive_passes_with_default_settings(self):
        # Smoke test: a normal small archive does not trigger any of
        # the new defenses with the default settings.
        buffer = self._build_zip_archive(
            members=[('a.txt', b'hello', zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)
        self.assertEqual(
            archive.member_contents(filename='a.txt'), b'hello'
        )
        with archive.open_member(filename='a.txt') as member:
            self.assertEqual(member.read(), b'hello')

    def test_member_contents_exceeds_size_maximum(self):
        # Cap at 4 bytes; the 16-byte member must be rejected before
        # the bytes are read into memory.
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        buffer = self._build_zip_archive(
            members=[('a.txt', b'X' * 16, zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        with self.assertRaises(
            expected_exception=ArchiveMemberSizeExceeded
        ):
            archive.member_contents(filename='a.txt')

    def test_open_member_exceeds_size_maximum(self):
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        buffer = self._build_zip_archive(
            members=[('a.txt', b'X' * 16, zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        with self.assertRaises(
            expected_exception=ArchiveMemberSizeExceeded
        ):
            archive.open_member(filename='a.txt')

    def test_member_at_exact_size_maximum_passes(self):
        # Boundary: a member whose declared size equals the cap is
        # allowed through. The cap is "exceeds", not "matches".
        setting_compressed_file_member_size_maximum.do_value_override(
            value=16
        )

        buffer = self._build_zip_archive(
            members=[('a.txt', b'X' * 16, zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='a.txt'), b'X' * 16
        )

    def test_member_size_check_disabled_with_zero(self):
        # Setting the cap to zero must disable the check entirely.
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        buffer = self._build_zip_archive(
            members=[('a.txt', b'X' * 1024, zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='a.txt'), b'X' * 1024
        )


class ZipArchiveCompressionRatioLimitTestCase(
    ArchiveZipFileBuilderMixin, CompressedFileSettingsResetMixin, BaseTestCase
):
    def test_high_ratio_member_is_rejected(self):
        # 64 KiB of zeros compresses to a few dozen bytes: ratio in
        # the thousands. Cap at 50; payload must be rejected.
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=50
        )
        # Disable the member-size check so the ratio check is what
        # we're really verifying.
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        buffer = self._build_zip_archive(
            members=[
                ('bomb.bin', b'\x00' * (64 * 1024), zipfile.ZIP_DEFLATED)
            ]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        with self.assertRaises(
            expected_exception=ArchiveCompressionRatioExceeded
        ):
            archive.member_contents(filename='bomb.bin')

    def test_low_ratio_member_passes(self):
        # Hash-derived bytes compress essentially not at all.
        # Must pass any sane ratio cap.
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=2
        )
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        content = b''.join(
            hashlib.sha256(i.to_bytes(2, 'big')).digest()
            for i in range(256)
        )
        buffer = self._build_zip_archive(
            members=[('a.bin', content, zipfile.ZIP_DEFLATED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='a.bin'), content
        )

    def test_stored_member_passes_ratio_check(self):
        # ZIP_STORED gives a 1:1 ratio. Must pass regardless of the
        # ratio cap.
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=2
        )
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        buffer = self._build_zip_archive(
            members=[('a.bin', b'X' * 4096, zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='a.bin'), b'X' * 4096
        )

    def test_zero_byte_member_passes_ratio_check(self):
        # Zero-byte member has compressed_size of zero. Must not
        # trigger ZeroDivisionError or false-positive the ratio.
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=50
        )
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        buffer = self._build_zip_archive(
            members=[('empty.bin', b'', zipfile.ZIP_STORED)]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='empty.bin'), b''
        )

    def test_ratio_check_disabled_with_zero(self):
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=0
        )
        setting_compressed_file_member_size_maximum.do_value_override(
            value=0
        )

        buffer = self._build_zip_archive(
            members=[
                ('bomb.bin', b'\x00' * (64 * 1024), zipfile.ZIP_DEFLATED)
            ]
        )
        archive = ZipArchive()
        archive._open(file_object=buffer)

        self.assertEqual(
            archive.member_contents(filename='bomb.bin'),
            b'\x00' * (64 * 1024)
        )


class EMLArchiveInputSizeLimitTestCase(CompressedFileSettingsResetMixin, BaseTestCase):
    def test_input_size_exceeds_maximum(self):
        # Set the input cap below the size of the sample EML fixture,
        # so the open call must raise before parsing.
        setting_compressed_file_input_size_maximum.do_value_override(
            value=8
        )

        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            with self.assertRaises(
                expected_exception=ArchiveInputSizeExceeded
            ):
                Archive.open(file_object=file_object)

    def test_input_size_at_default_passes(self):
        # Smoke: the EML fixture loads fine with default settings.
        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                isinstance(archive, EMLArchive)
            )

    def test_input_size_check_disabled_with_zero(self):
        setting_compressed_file_input_size_maximum.do_value_override(
            value=0
        )

        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                isinstance(archive, EMLArchive)
            )

    def test_member_size_check_after_input_check(self):
        # The member-size check must still fire once parsing has
        # completed, in case the input was within the input cap but a
        # single part is enormous.
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)

            with self.assertRaises(
                expected_exception=ArchiveMemberSizeExceeded
            ):
                archive.member_contents(filename='body')


class MsgArchiveInputSizeLimitTestCase(CompressedFileSettingsResetMixin, BaseTestCase):
    def test_input_size_exceeds_maximum(self):
        setting_compressed_file_input_size_maximum.do_value_override(
            value=8
        )

        with open(file=TEST_ARCHIVE_MSG_STRANGE_DATE_PATH, mode='rb') as file_object:
            with self.assertRaises(
                expected_exception=ArchiveInputSizeExceeded
            ):
                Archive.open(file_object=file_object)

    def test_member_size_check_after_input_check(self):
        setting_compressed_file_member_size_maximum.do_value_override(
            value=4
        )

        with open(file=TEST_ARCHIVE_MSG_STRANGE_DATE_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)

            with self.assertRaises(
                expected_exception=ArchiveMemberSizeExceeded
            ):
                archive.member_contents(filename='message.txt')


class PDFArchiveInputSizeLimitTestCase(CompressedFileSettingsResetMixin, BaseTestCase):
    def test_input_size_exceeds_maximum(self):
        setting_compressed_file_input_size_maximum.do_value_override(
            value=8
        )

        with open(file=TEST_PDF_WITH_ATTACHMENT_PATH, mode='rb') as file_object:
            with self.assertRaises(
                expected_exception=ArchiveInputSizeExceeded
            ):
                Archive.open(file_object=file_object)

    def test_member_size_check_after_input_check(self):
        # Cap below the size of the bundled PDF attachment (6669 bytes
        # per the existing test).
        setting_compressed_file_member_size_maximum.do_value_override(
            value=128
        )

        with open(file=TEST_PDF_WITH_ATTACHMENT_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)

            with self.assertRaises(
                expected_exception=ArchiveMemberSizeExceeded
            ):
                archive.open_member(filename='0-image.png')

    def test_input_size_check_disabled_with_zero(self):
        setting_compressed_file_input_size_maximum.do_value_override(
            value=0
        )

        with open(file=TEST_PDF_WITH_ATTACHMENT_PATH, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                isinstance(archive, PDFArchive)
            )


class ArchiveNonSeekableInputTestCase(
    ArchiveZipFileBuilderMixin, CompressedFileSettingsResetMixin, BaseTestCase
):
    class _NonSeekableWrapper:
        """
        A file-like wrapper that exposes only ``read``. Calling
        ``tell`` or ``seek`` on it raises ``AttributeError`` (the
        attributes are not defined), which is the signal
        ``_get_seekable_size`` uses to identify a non-seekable input.
        """

        def __init__(self, file_object):
            self._file_object = file_object

        def read(self, size=-1):
            return self._file_object.read(size)

    def test_get_seekable_size_returns_none_for_non_seekable(self):
        # A wrapper lacking ``tell``/``seek`` must yield ``None``, not raise.
        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            wrapper = self._NonSeekableWrapper(file_object=file_object)
            self.assertIsNone(
                Archive._get_seekable_size(file_object=wrapper)
            )

    def test_check_input_size_skips_for_non_seekable(self):
        # Tolerate a non-seekable input by silently skipping, rather than
        # letting the ``AttributeError`` from a missing ``tell`` propagate or
        # raising ``ArchiveInputSizeExceeded`` against an unknown
        # size.
        setting_compressed_file_input_size_maximum.do_value_override(
            value=8
        )

        with open(file=TEST_ARCHIVE_EML_SAMPLE_PATH, mode='rb') as file_object:
            wrapper = self._NonSeekableWrapper(file_object=file_object)
            archive = ZipArchive()
            # Must not raise.
            archive._check_input_size(file_object=wrapper)

    def test_check_input_size_skips_for_pipe_like(self):
        setting_compressed_file_input_size_maximum.do_value_override(
            value=8
        )

        class _PipeLikeWrapper:
            # A file-like whose ``tell``/``seek`` are defined but raise
            # ``OSError`` (e.g. a pipe or socket) must also be treated as
            # "size unknown", not as an error.

            def read(self, size=-1):
                return b''

            def seek(self, *args, **kwargs):
                raise OSError('not seekable')

            def tell(self):
                raise OSError('not seekable')

        wrapper = _PipeLikeWrapper()
        archive = ZipArchive()
        archive._check_input_size(file_object=wrapper)
