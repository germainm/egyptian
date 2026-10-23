import logging

from django.apps import apps
from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.settings import setting_image_generation_timeout
from mayan.apps.lock_manager.backends.base import LockingBackend

from .classes import OCRBackendBase
from .events import (
    event_ocr_document_version_content_deleted,
    event_ocr_document_version_finished
)
from .exceptions import OCRError
from .literals import ERROR_LOG_DOMAIN_NAME

logger = logging.getLogger(name=__name__)


class DocumentVersionPageOCRContentManager(models.Manager):
    def delete_content_for(self, document_version, user=None):
        self.filter(document_version_page__document_version=document_version).delete()

        event_ocr_document_version_content_deleted.commit(
            actor=user, action_object=document_version.document,
            target=document_version
        )

    def do_ocr_finished(self, document_version, user):
        event_ocr_document_version_finished.commit(
            action_object=document_version.document, actor=user,
            target=document_version
        )

    def process_document_version_page(self, document_version_page, user=None):
        logger.debug(
            'Processing page: %d of document version: %s',
            document_version_page.page_number,
            document_version_page.document_version
        )

        DocumentVersionPageOCRContent = apps.get_model(
            app_label='ocr', model_name='DocumentVersionPageOCRContent'
        )

        backend_instance = OCRBackendBase.get_instance()

        lock_name = document_version_page.get_lock_name(user=user)

        lock_timeout = setting_image_generation_timeout.value * 2 + backend_instance.get_task_time_limit()

        try:
            document_version_page_lock = LockingBackend.get_backend().acquire_lock(
                name=lock_name, timeout=lock_timeout
            )
        except Exception as exception:
            logger.error(
                'Error attempting to lock document version page: %d; %s',
                document_version_page.pk, exception, exc_info=True
            )
            raise
        else:
            try:
                cache_filename = document_version_page.generate_image(
                    _acquire_lock=False, user=user
                )

                with document_version_page.cache_partition.get_file(filename=cache_filename).open() as file_object:
                    try:
                        ocr_content = backend_instance.execute(
                            file_object=file_object,
                            language=document_version_page.document_version.document.language
                        )
                    except OCRError as exception:
                        error_log_text = _(
                            message='Error calling OCR backend for page: '
                            '%(page_number)d; %(exception)s'
                        ) % {
                            'exception': exception,
                            'page_number': document_version_page.page_number
                        }
                        document_version_page.error_log.create(
                            domain_name=ERROR_LOG_DOMAIN_NAME,
                            text=error_log_text
                        )
                    else:
                        DocumentVersionPageOCRContent.objects.update_or_create(
                            document_version_page=document_version_page,
                            defaults={'content': ocr_content}
                        )
            except Exception as exception:
                logger.error(
                    'OCR error for document version page: %d; %s',
                    document_version_page.pk, exception, exc_info=True
                )
                raise
            else:
                logger.debug(
                    'Finished processing page: %d of document version: %s',
                    document_version_page.page_number,
                    document_version_page.document_version
                )
            finally:
                document_version_page_lock.release()


class DocumentTypeSettingsManager(models.Manager):
    def get_by_natural_key(self, document_type_natural_key):
        DocumentType = apps.get_model(
            app_label='documents', model_name='DocumentType'
        )
        try:
            document_type = DocumentType.objects.get_by_natural_key(
                document_type_natural_key
            )
        except DocumentType.DoesNotExist:
            raise self.model.DoesNotExist

        return self.get(document_type__pk=document_type.pk)
