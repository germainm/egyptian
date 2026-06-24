import glob
import importlib
from io import BytesIO
import logging
import os
from pathlib import Path
import shutil
import tarfile
import zipfile

import psutil

from django.conf import settings
from django.core.files.base import ContentFile

from mayan.apps.common.tests.literals import (
    TEST_COMPRESSED_FILE_CONTENTS, TEST_FILE3_PATH, TEST_FILE_CONTENTS_1,
    TEST_FILENAME1, TEST_FILENAME3
)
from mayan.apps.documents.literals import STORAGE_NAME_DOCUMENT_FILES
from mayan.apps.permissions.tests.mixins import PermissionTestMixin
from mayan.apps.smart_settings.setting_clusters import setting_cluster
from mayan.apps.smart_settings.utils import get_environment_variable_full_name

from ..classes import DefinedStorage
from ..compressed_files import Archive
from ..literals import (
    DEFAULT_STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM,
    DEFAULT_STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM,
    DEFAULT_STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM
)
from ..models import DownloadFile, SharedUploadedFile
from ..settings import (
    setting_compressed_file_compression_ratio_maximum,
    setting_compressed_file_input_size_maximum,
    setting_compressed_file_member_size_maximum,
    setting_temporary_directory
)
from ..utils import mkdtemp

from .literals import (
    TEST_DOWNLOAD_FILE_CONTENT_FILE_NAME, TEST_SHARED_UPLOADED_FILE_FILENAME
)


class ArchiveClassTestCaseMixin:
    archive_path = None
    cls = None
    filename = TEST_FILENAME3
    file_path = TEST_FILE3_PATH
    members_list = TEST_COMPRESSED_FILE_CONTENTS
    member_name = TEST_FILENAME1
    member_contents = TEST_FILE_CONTENTS_1

    def test_add_file(self):
        archive = self.cls()
        archive.create()
        with open(file=self.file_path, mode='rb') as file_object:
            archive.add_file(file_object=file_object, filename=self.filename)
            self.assertEqual(
                archive.members(), [self.filename]
            )

    def test_open(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertTrue(
                isinstance(archive, self.cls)
            )

    def test_members(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertEqual(
                archive.members(), self.members_list
            )

    def test_member_contents(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            self.assertEqual(
                archive.member_contents(filename=self.member_name),
                self.member_contents
            )

    def test_open_member(self):
        with open(file=self.archive_path, mode='rb') as file_object:
            archive = Archive.open(file_object=file_object)
            file_object = archive.open_member(filename=self.member_name)
            self.assertEqual(
                file_object.read(), self.member_contents
            )


class ArchiveZipFileBuilderMixin:
    def _build_zip_archive(self, members):
        buffer = BytesIO()
        with zipfile.ZipFile(file=buffer, mode='w') as archive:
            for filename, content, compression in members:
                archive.writestr(
                    zinfo_or_arcname=filename, data=content,
                    compress_type=compression
                )

        buffer.seek(0)
        return buffer


class ArchiveTarFileBuilderMixin:
    def _build_tar_archive(self, members):
        buffer = BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            for filename, content in members:
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(content)
                archive.addfile(tarinfo=tarinfo, fileobj=BytesIO(content))

        buffer.seek(0)
        return buffer


class CompressedFileSettingsResetMixin:
    def tearDown(self):
        setting_compressed_file_compression_ratio_maximum.do_value_override(
            value=DEFAULT_STORAGE_COMPRESSED_FILE_COMPRESSION_RATIO_MAXIMUM
        )
        setting_compressed_file_input_size_maximum.do_value_override(
            value=DEFAULT_STORAGE_COMPRESSED_FILE_INPUT_SIZE_MAXIMUM
        )
        setting_compressed_file_member_size_maximum.do_value_override(
            value=DEFAULT_STORAGE_COMPRESSED_FILE_MEMBER_SIZE_MAXIMUM
        )
        super().tearDown()


class DescriptorLeakCheckTestCaseMixin:
    _skip_file_descriptor_test = False

    def _get_process_descriptor_count(self):
        process = psutil.Process()
        return process.num_fds()

    def _get_process_descriptors(self):
        process = psutil.Process()._proc
        return os.listdir(
            path='{}/{}/fd'.format(process._procfs_path, process.pid)
        )

    def setUp(self):
        super().setUp()
        self._process_descriptor_count = self._get_process_descriptor_count()
        self._process_descriptors = self._get_process_descriptors()

    def tearDown(self):
        if not self._skip_file_descriptor_test:
            if self._get_process_descriptor_count() > self._process_descriptor_count:
                raise ValueError(
                    'File descriptor leak. The number of file descriptors '
                    'at the end are higher than at the start of the test.'
                )

            for descriptor in self._get_process_descriptors():
                if descriptor not in self._process_descriptors:
                    raise ValueError(
                        'File descriptor leak. A descriptor was found at '
                        'the end of the test that was not present at the '
                        'start of the test.'
                    )

        super().tearDown()


class DownloadFileAPIViewTestMixin:
    def _request_test_download_file_delete_api_view(self):
        return self.delete(
            viewname='rest_api:download_file-detail',
            kwargs={'download_file_id': self._test_download_file.pk}
        )

    def _request_test_download_file_detail_api_view(self):
        return self.get(
            viewname='rest_api:download_file-detail',
            kwargs={'download_file_id': self._test_download_file.pk}
        )

    def _request_test_download_file_download_api_view(self):
        return self.get(
            viewname='rest_api:download_file-download',
            kwargs={'download_file_id': self._test_download_file.pk}
        )

    def _request_test_download_file_list_api_view(self):
        return self.get(viewname='rest_api:download_file-list')


class DownloadFileTestMixin(PermissionTestMixin):
    def setUp(self):
        super().setUp()
        self._test_download_file_list = []

    def _create_test_download_file(self, content=None, user=None):
        file_content = None

        test_download_file_count = len(
            self._test_download_file_list
        )

        test_download_file_filename = '{}_{}'.format(
            TEST_DOWNLOAD_FILE_CONTENT_FILE_NAME,
            test_download_file_count
        )

        if content:
            file_content = ContentFile(
                content=content, name=test_download_file_filename
            )

        self._test_download_file = DownloadFile.objects.create(
            file=file_content, user=user or self._test_case_user
        )

        self._test_download_file_list.append(self._test_download_file)


class DownloadFileViewTestMixin:
    def _request_test_download_file_delete_view(self):
        return self.post(
            viewname='storage:download_file_delete', kwargs={
                'download_file_id': self._test_download_file.pk
            }
        )

    def _request_test_download_file_download_view(self):
        return self.get(
            viewname='storage:download_file_download', kwargs={
                'download_file_id': self._test_download_file.pk
            }
        )

    def _request_test_download_file_list_view(self):
        return self.get(viewname='storage:download_file_list')


class OpenFileCheckTestCaseMixin:
    _skip_open_file_leak_test = False

    def _get_open_files(self):
        process = psutil.Process()
        return process.open_files()

    def setUp(self):
        super().setUp()

        self._open_files = self._get_open_files()

    def tearDown(self):
        if not self._skip_open_file_leak_test:
            for new_open_file in self._get_open_files():
                if new_open_file not in self._open_files:
                    raise ValueError(
                        'File left open: {}'.format(new_open_file)
                    )

        super().tearDown()


class StorageProcessorTestMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.defined_storage = DefinedStorage.get(
            name=STORAGE_NAME_DOCUMENT_FILES
        )
        cls.document_storage_dotted_path = cls.defined_storage.dotted_path
        cls.document_storage_kwargs = cls.defined_storage.kwargs

    def setUp(self):
        super().setUp()
        self.temporary_directory = mkdtemp()
        self.path_temporary_directory = Path(self.temporary_directory)
        self.path_test_file = self.path_temporary_directory / 'test_file.txt'

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(path=self.temporary_directory, ignore_errors=True)
        self.defined_storage.dotted_path = self.document_storage_dotted_path
        self.defined_storage.kwargs = self.document_storage_kwargs


class SharedUploadedFileTestMixin:
    def setUp(self):
        super().setUp()
        self._test_shared_uploaded_file_list = []

    def _create_test_shared_uploaded_file(self, content=None):
        file_content = None

        test_shared_uploaded_file_count = len(
            self._test_shared_uploaded_file_list
        )
        test_shared_uploaded_file_filename = '{}_{}'.format(
            TEST_SHARED_UPLOADED_FILE_FILENAME,
            test_shared_uploaded_file_count
        )

        if content:
            file_content = ContentFile(
                content=content, name=test_shared_uploaded_file_filename
            )

        self._test_shared_uploaded_file = SharedUploadedFile.objects.create(
            file=file_content, filename=test_shared_uploaded_file_filename
        )
        self._test_shared_uploaded_file_list.append(
            self._test_shared_uploaded_file
        )


class StorageSettingTestMixin:
    def _test_storage_setting_with_invalid_value(
        self, setting, storage_module, storage_name
    ):
        old_value = setting.value
        setting_cluster.do_cache_invalidate()

        environment_variable_name = get_environment_variable_full_name(
            name=setting.global_name
        )
        self._set_environment_variable(
            name=environment_variable_name, value='invalid_value'
        )
        self.test_case_silenced_logger_new_level = logging.FATAL + 10
        self._silence_logger(name='mayan.apps.storage.classes')

        with self.assertRaises(expected_exception=TypeError) as assertion:
            importlib.reload(storage_module)
            defined_storage = DefinedStorage.get(name=storage_name)
            defined_storage.get_storage_instance()

        setting.do_value_override(value=old_value)
        importlib.reload(storage_module)

        return assertion


class TempfileCheckTestCasekMixin:
    # Ignore the jvmstat instrumentation and GitLab's CI .config files.
    # Ignore LibreOffice fontconfig cache dir.
    ignore_globs = ('hsperfdata_*', '.config', '.cache')

    def _get_temporary_entries(self):
        ignored_result = []

        # Expand globs by joining the temporary directory and then flattening
        # the list of lists into a single list.
        for item in self.ignore_globs:
            ignored_result.extend(
                glob.glob(
                    os.path.join(setting_temporary_directory.value, item)
                )
            )

        # Remove the path and leave only the expanded filename.
        ignored_result = map(lambda x: os.path.split(x)[-1], ignored_result)

        return set(
            os.listdir(setting_temporary_directory.value)
        ) - set(ignored_result)

    def setUp(self):
        super().setUp()
        if getattr(settings, 'COMMON_TEST_TEMP_FILES', False):
            self._temporary_items = self._get_temporary_entries()

    def tearDown(self):
        if getattr(settings, 'COMMON_TEST_TEMP_FILES', False):
            final_temporary_items = self._get_temporary_entries()
            self.assertEqual(
                self._temporary_items, final_temporary_items,
                msg='Orphan temporary file. The number of temporary '
                'files and/or directories at the start and at the end of '
                'the test are not the same. Orphan entries: {}'.format(
                    ','.join(final_temporary_items - self._temporary_items)
                )
            )
        super().tearDown()
