import hashlib
from io import BytesIO
from itertools import islice
import logging
import shutil
import time

from django.apps import apps
from django.db import IntegrityError
from django.template.defaultfilters import filesizeformat
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.signals import signal_mayan_pre_save
from mayan.apps.converter.classes import ConverterBase
from mayan.apps.converter.exceptions import (
    AppImageError, InvalidOfficeFormat, PageCountError
)
from mayan.apps.databases.classes import ModelQueryFields
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter
from mayan.apps.file_caching.models import CachePartitionFile
from mayan.apps.mime_types.classes import MIMETypeBackend
from mayan.apps.storage.hashing import chunk_hash_file_object
from mayan.apps.storage.model_mixins import ModelMixinFileFieldOpen

from ..classes import DocumentFileAction
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


def _read_cache_file(cache_file):
    """
    Lit le contenu d'un CachePartitionFile en mémoire et retourne un BytesIO.
    Ceci évite la race condition entre storage.exists() et open() — le fichier
    physique est lu immédiatement pendant que le lock est tenu, avant que le
    pruning ne puisse le supprimer.
    """
    with cache_file.open() as f:
        return BytesIO(f.read())


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
            name='file-{}'.format(self.uuid)
        )
        return partition

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
        """
        Returns a boolean value that indicates if the document's file
        exists in storage. Returns True if the document's file is verified to
        be in the document storage. This is a diagnostic flag to help users
        detect if the storage has desynchronized (ie: Amazon's S3).
        """
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
        cache_filename = 'intermediate_file'

        # Étape 1 — chercher le fichier dans le cache DB.
        try:
            cache_file = self.cache_partition.get_file(
                filename=cache_filename
            )
        except CachePartitionFile.DoesNotExist:
            logger.debug(msg='Intermediate file not found in cache.')
        else:
            logger.debug(msg='Intermediate file found in cache DB.')
            storage_instance = self.cache_partition.cache.storage
            if not storage_instance.exists(name=cache_file.full_filename):
                # Cas A : worker gagnant en train d'écrire (transitoire)
                # → attendre jusqu'à 10s qu'il apparaisse.
                # Cas B : fichier purgé par pruning (orphelin permanent)
                # → après 10s, supprimer l'entrée DB et régénérer.
                logger.warning(
                    'Intermediate file DB entry exists but physical file '
                    'is missing for partition %s — waiting up to 10s.',
                    self.cache_partition.pk
                )
                for _attempt in range(20):
                    time.sleep(0.5)
                    if storage_instance.exists(
                        name=cache_file.full_filename
                    ):
                        logger.debug(
                            'Intermediate file appeared after %d attempts '
                            'for partition %s.',
                            _attempt + 1, self.cache_partition.pk
                        )
                        # Lire en mémoire immédiatement pour éviter
                        # une nouvelle race condition avec le pruning.
                        return _read_cache_file(cache_file)
                # Après 10s toujours absent → orphelin confirmé
                logger.warning(
                    'Intermediate file still missing after 10s for '
                    'partition %s — deleting orphan DB entry and '
                    'regenerating.',
                    self.cache_partition.pk
                )
                cache_file.delete()
            else:
                # Lire en mémoire immédiatement — évite la race condition
                # entre exists() et l'ouverture réelle dans get_image().
                return _read_cache_file(cache_file)

        # Étape 2 — générer l'intermediate_file.
        try:
            with self.open() as file_object:
                converter = ConverterBase.get_converter_class()(
                    file_object=file_object
                )
                with converter.to_pdf() as pdf_file_object:
                    try:
                        with self.cache_partition.create_file(
                            filename=cache_filename
                        ) as file_object:
                            shutil.copyfileobj(
                                fsrc=pdf_file_object, fdst=file_object
                            )
                    except IntegrityError:
                        # Race condition : autre worker a créé le fichier
                        # entre notre DoesNotExist et notre create_file.
                        # Avec blocking=True le lock devrait prévenir ça,
                        # mais on garde ce filet de sécurité.
                        logger.debug(
                            'Race condition on intermediate_file for '
                            'partition %s — waiting for winning worker.',
                            self.cache_partition.pk
                        )
                        for _attempt in range(10):
                            try:
                                return _read_cache_file(
                                    self.cache_partition.get_file(
                                        filename=cache_filename
                                    )
                                )
                            except CachePartitionFile.DoesNotExist:
                                time.sleep(0.5)
                        return _read_cache_file(
                            self.cache_partition.get_file(
                                filename=cache_filename
                            )
                        )

                    return _read_cache_file(
                        self.cache_partition.get_file(
                            filename=cache_filename
                        )
                    )

        except InvalidOfficeFormat:
            return self.open()
        except Exception as exception:
            from mayan.apps.lock_manager.exceptions import LockError
            if isinstance(exception, LockError):
                raise
            logger.error(
                'Error creating intermediate file "%s"; %s.',
                cache_filename, exception, exc_info=True
            )
            try:
                self.cache_partition.get_file(
                    filename=cache_filename
                ).delete()
            except CachePartitionFile.DoesNotExist:
                pass
            raise exception

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
            error_log_text = _(
                message='Error updating page count; %(exception)s'
            ) % {'exception': exception}

            self.error_log.create(
                domain_name=ERROR_LOG_DOMAIN_NAME, text=error_log_text
            )
            raise
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

    def save_to_file(self, file_object):
        with self.open() as input_file_object:
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
