import mimetypes
import hashlib
from itertools import islice
import logging
import shutil

from django.apps import apps
from django.template.defaultfilters import filesizeformat
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.signals import signal_mayan_pre_save
from mayan.apps.converter.classes import ConverterBase
from mayan.apps.converter.exceptions import AppImageError, PageCountError
from mayan.apps.databases.classes import ModelQueryFields
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter
from mayan.apps.mime_types.classes import MIMETypeBackend
from mayan.apps.storage.hashing import chunk_hash_file_object
from mayan.apps.storage.model_mixins import ModelMixinFileFieldOpen

from ..classes import DocumentFileAction

# MIME types that mimetypes.guess_type() may return for text/plain files and
# that the converter has a dedicated rendering path for.  Only these are
# promoted when libmagic falls back to text/plain.
_MIME_TYPE_EXTENSION_OVERRIDES = frozenset((
    'text/markdown',
    'text/x-markdown',
    'image/vnd.dxf',
    'application/dxf',
    'application/x-autocad',
    'application/x-dxf',
    'model/stl',
    'model/x.stl-ascii',
    'model/x.stl-binary',
    'application/sla',
))

from ..events import event_document_file_created, event_document_file_edited
from ..literals import (
    DOCUMENT_FILE_PAGE_CREATE_BATCH_SIZE, ERROR_LOG_DOMAIN_NAME,
    IMAGE_ERROR_DOCUMENT_FILE_HAS_NO_PAGES,
    STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE
)
from ..permissions import permission_document_file_view
from ..settings import setting_hash_block_size
from ..signals import signal_post_document_file_upload

logger = logging.getLogger(name=__name__)



class DocumentFileBusinessLogicMixin(ModelMixinFileFieldOpen):
    @staticmethod
    def hash_function():
        return hashlib.sha256()

    @classmethod
    def execute_pre_create_hooks(cls, kwargs=None):
        cls._execute_hooks(
            hook_list=cls._hooks_pre_create, instance=None, kwargs=kwargs
        )

    @classmethod
    def register_post_save_hook(cls, func, order=None):
        cls._insert_hook_entry(
            hook_list=cls._post_save_hooks, func=func, order=order
        )

    @classmethod
    def register_pre_create_hook(cls, func, order=None):
        cls._insert_hook_entry(
            hook_list=cls._hooks_pre_create, func=func, order=order
        )

    @classmethod
    def register_pre_open_hook(cls, func, order=None):
        cls._insert_hook_entry(
            hook_list=cls._pre_open_hooks, func=func, order=order
        )

    @classmethod
    def register_pre_save_hook(cls, func, order=None):
        cls._insert_hook_entry(
            hook_list=cls._pre_save_hooks, func=func, order=order
        )

    @method_event(
        action_object='document',
        event_manager_class=EventManagerMethodAfter,
        event=event_document_file_created,
        target='self'
    )
    def _create(self, *args, **kwargs):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        self._event_keep_attributes = ('_event_actor',)
        user = getattr(self, '_event_actor', None)

        logger.debug('Creating new file for document: %s', self.document)
        DocumentFile.execute_pre_create_hooks(
            kwargs={
                'document': self.document,
                'file_object': self.file.open(mode='rb'),
                'user': user
            }
        )

        try:
            self._event_ignore = True
            result = self._save(*args, **kwargs)

            logger.debug(
                'New document file "%s" created for document: %s',
                self, self.document
            )

            self.document.file_latest = self
            self.document.is_stub = False

            if not self.document.label:
                self.document.label = str(self)

            self.document._event_ignore = True
            self.document.save(
                update_fields=('file_latest', 'is_stub', 'label')
            )
        except Exception as exception:
            logger.error(
                'Error creating new document file for document "%s"; %s',
                self.document, exception, exc_info=True
            )
            raise
        else:
            return result

    def _introspect(self):
        actor = getattr(self, '_event_actor', None)

        try:
            self.checksum_update(save=False)
            super().save(
                update_fields=('checksum',)
            )

            self.mimetype_update(save=False)
            super().save(
                update_fields=('encoding', 'mimetype',)
            )

            self.size_update(save=False)
            super().save(
                update_fields=('size',)
            )

            self.page_count_update(save=False)
        except Exception as exception:
            logger.error(
                'Error introspecting new document file for document '
                '"%s"; %s', self.document, exception, exc_info=True
            )
            raise
        else:
            event_document_file_edited.commit(
                action_object=self.document, actor=actor, target=self
            )

            self.upload_complete()

    def _open(self, raw=False, **kwargs):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        if raw:
            return self.file.storage.open(**kwargs)
        else:
            file_object = self.file.storage.open(**kwargs)

            result = DocumentFile._execute_hooks(
                hook_list=DocumentFile._pre_open_hooks,
                instance=self, file_object=file_object
            )

            if result:
                return result['file_object']
            else:
                return file_object

    @method_event(
        action_object='document',
        event_manager_class=EventManagerMethodAfter,
        event=event_document_file_edited,
        target='self'
    )
    def _save(self, *args, **kwargs):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        user = getattr(self, '_event_actor', None)

        try:
            self.execute_pre_save_hooks()

            signal_mayan_pre_save.send(
                instance=self, sender=DocumentFile, user=user
            )

            result = super().save(*args, **kwargs)

            DocumentFile._execute_hooks(
                hook_list=DocumentFile._post_save_hooks,
                instance=self
            )
        except Exception as exception:
            logger.error(
                'Error saving document file for document "%s"; %s',
                self.document, exception, exc_info=True
            )
            raise
        else:
            return result

    @cached_property
    def cache(self):
        Cache = apps.get_model(app_label='file_caching', model_name='Cache')
        return Cache.objects.get(
            defined_storage_name=STORAGE_NAME_DOCUMENT_FILE_PAGE_IMAGE_CACHE
        )

    @cached_property
    def cache_partition(self):
        partition, created = self.cache.partitions.get_or_create(
            name=self.cache_partition_name
        )
        return partition

    @property
    def cache_partition_name(self):
        return 'file-{}'.format(self.uuid)

    def cache_partition_delete(self):
        for partition in self.cache.partitions.filter(
            name=self.cache_partition_name
        ):
            partition.delete()

    def checksum_update(self, save=True):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        block_size = setting_hash_block_size.value
        if block_size == 0:
            block_size = -1

        if self.exists():
            with self.open(raw=True) as file_object:
                hash_object = chunk_hash_file_object(
                    block_size=block_size, file_object=file_object,
                    hash_function=DocumentFile.hash_function
                )

            hash_object_hexdigest = hash_object.hexdigest()
            self.checksum = str(hash_object_hexdigest)

            if save:
                self.save(
                    update_fields=('checksum',)
                )

            return self.checksum

    def execute_pre_save_hooks(self):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        DocumentFile._execute_hooks(
            hook_list=DocumentFile._pre_save_hooks, instance=self
        )

    def exists(self):
        name = self.file.name
        self.file.close()

        return self.file.storage.exists(name=name)

    def get_api_image_url(
        self, maximum_layer_order=None, transformation_instance_list=None,
        user=None
    ):
        first_page = self.pages.first()
        if first_page:
            return first_page.get_api_image_url(
                maximum_layer_order=maximum_layer_order,
                transformation_instance_list=transformation_instance_list,
                user=user
            )
        else:
            raise AppImageError(
                error_name=IMAGE_ERROR_DOCUMENT_FILE_HAS_NO_PAGES
            )

    def get_cache_partitions(self):
        result = [self.cache_partition]
        for page in self.file_pages.all():
            result.append(page.cache_partition)

        return result

    def get_document_file_latest(self):
        return self.document.files.exclude(pk=self.pk).order_by('timestamp').only('id').last()

    def get_intermediate_file(self):
        return ConverterBase.get_intermediate_file(
            cache_partition=self.cache_partition, mime_type=self.mimetype,
            source_file_object_opener=self.open
        )

    def get_label(self):
        return self.filename
    get_label.short_description = _(message='Label')

    def get_page_count(self, user):
        queryset_pages = self.pages.all()
        queryset_pages = AccessControlList.objects.restrict_queryset(
            permission=permission_document_file_view,
            queryset=queryset_pages, user=user
        )

        return queryset_pages.count()
    get_page_count.short_description = _(message='Pages')

    def get_size_display(self):
        return filesizeformat(bytes_=self.size)

    get_size_display.short_description = _(message='Size')

    @property
    def is_in_trash(self):
        return self.document.is_in_trash

    def mimetype_update(self, save=True):
        if self.exists():
            try:
                with self.open() as file_object:
                    mimetype_backend = MIMETypeBackend.get_backend_instance()
                    self.mimetype, self.encoding = mimetype_backend.get_mime_type(
                        file_object=file_object
                    )
                # When libmagic returns the generic text/plain, refine using
                # the original filename extension for formats that have a
                # dedicated converter path (e.g. .md to text/markdown so it
                # goes through the markdown renderer instead of LibreOffice).
                # Only override to MIME types the converter explicitly handles
                # to avoid breaking unknown formats.
                if self.mimetype == 'text/plain' and self.filename:
                    guessed = mimetypes.guess_type(self.filename)[0]
                    if guessed and guessed in _MIME_TYPE_EXTENSION_OVERRIDES:
                        self.mimetype = guessed
            except Exception:
                self.encoding = ''
                self.mimetype = ''
            finally:
                if save:
                    self.save(
                        update_fields=('encoding', 'mimetype')
                    )

    def page_count_update(self, save=True, user=None):
        try:
            with self.open() as file_object:
                converter_class = ConverterBase.get_converter_class()
                converter = converter_class(
                    file_object=file_object, mime_type=self.mimetype
                )
                detected_pages = converter.get_page_count()
        except PageCountError as exception:
            """Converter backend doesn't understand the format."""
            error_log_text = _(
                message='Error updating page count; %(exception)s'
            ) % {'exception': exception}

            self.error_log.create(
                domain_name=ERROR_LOG_DOMAIN_NAME, text=error_log_text
            )
        else:
            DocumentFilePage = apps.get_model(
                app_label='documents', model_name='DocumentFilePage'
            )

            for page in self.pages.all():
                page._event_actor = user
                page._event_ignore = True
                page.delete()

            document_file_pages = (
                DocumentFilePage(
                    document_file=self, page_number=page_number + 1
                ) for page_number in range(detected_pages)
            )

            while True:
                batch = list(
                    islice(
                        document_file_pages,
                        DOCUMENT_FILE_PAGE_CREATE_BATCH_SIZE
                    )
                )

                if not batch:
                    break

                DocumentFilePage.objects.bulk_create(
                    batch_size=DOCUMENT_FILE_PAGE_CREATE_BATCH_SIZE,
                    objs=batch
                )

            if save:
                self._event_actor = user
                self.save()

            return detected_pages

    @property
    def pages(self):
        DocumentFilePage = apps.get_model(
            app_label='documents', model_name='DocumentFilePage'
        )
        queryset = ModelQueryFields.get(model=DocumentFilePage).get_queryset()
        return queryset.filter(
            pk__in=self.file_pages.values('pk')
        )

    @property
    def pages_first(self):
        return self.pages.first()

    def save_to_file(self, file_object, raw=False):
        with self.open(raw=raw) as input_file_object:
            shutil.copyfileobj(fsrc=input_file_object, fdst=file_object)

    def size_update(self, save=True):
        if self.exists():
            name = self.file.name
            self.file.close()
            self.size = self.file.storage.size(name=name)

            if save:
                self.save(
                    update_fields=('size',)
                )

    def upload_complete(self):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        signal_post_document_file_upload.send(
            sender=DocumentFile, instance=self
        )

    @property
    def uuid(self):
        return '{}-{}'.format(self.document.uuid, self.pk)

    def versions_new(self, action_name, comment=None, user=None):
        DocumentFileAction.get(name=action_name).execute(
            comment=comment, document=self.document, document_file=self,
            user=user
        )

    versions_new.help_text = _(
        message='Controls what happens when a new document file is uploaded.'
    )
