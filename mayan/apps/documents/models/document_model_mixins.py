import logging
from pathlib import Path

from django.apps import apps
from django.core.files import File
from django.utils.translation import gettext, gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.converter.exceptions import AppImageError

from ..events import event_document_type_changed
from ..literals import (
    DEFAULT_DOCUMENT_FILE_ACTION_NAME,
    IMAGE_ERROR_DOCUMENT_VERSION_ACTIVE_MISSING
)
from ..permissions import permission_document_change_type
from ..signals import signal_post_document_type_change

from .document_type_models import DocumentType

logger = logging.getLogger(name=__name__)


class DocumentBusinessLogicMixin:
    @classmethod
    def execute_pre_create_hooks(cls, kwargs=None):
        cls._execute_hooks(
            hook_list=cls._hooks_pre_create, kwargs=kwargs
        )

    @classmethod
    def register_pre_create_hook(cls, func, order=None):
        cls._insert_hook_entry(
            hook_list=cls._hooks_pre_create, func=func, order=order
        )

    def _document_type_change(self, document_type, force=False, user=None):
        has_changed = self.document_type != document_type

        if has_changed or force:
            self.document_type = document_type

            self._event_ignore = True
            self.save(
                update_fields=('document_type',)
            )

            if user:
                self.add_as_recent_document_for_user(user=user)

            signal_post_document_type_change.send(
                sender=self.__class__, instance=self
            )

            event_document_type_changed.commit(
                action_object=document_type, actor=user, target=self
            )

    def add_as_recent_document_for_user(self, user):
        RecentlyAccessedDocument = apps.get_model(
            app_label='documents', model_name='RecentlyAccessedDocument'
        )
        return RecentlyAccessedDocument.valid.add_document_for_user(
            document=self, user=user
        )

    def document_type_change(self, document_type, user, force=False):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        queryset = AccessControlList.objects.restrict_queryset(
            queryset=Document.valid.all(),
            permission=permission_document_change_type,
            user=user
        )

        queryset.get(pk=self.pk)

        queryset = AccessControlList.objects.restrict_queryset(
            queryset=DocumentType.objects.all(),
            permission=permission_document_change_type,
            user=user
        )

        document_type = queryset.get(pk=document_type.pk)

        return self._document_type_change(
            document_type=document_type, force=force, user=user
        )

    def files_upload(
        self, file_object, action_name=None, comment=None, filename=None,
        user=None
    ):
        logger.debug('Creating new document file for document: %s', self)

        if not action_name:
            action_name = DEFAULT_DOCUMENT_FILE_ACTION_NAME

        if not comment:
            comment = ''

        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )

        try:
            filename = filename or Path(file_object.name).name

            document_file = DocumentFile(
                document=self, comment=comment, file=File(file=file_object),
                filename=filename
            )
            document_file._event_actor = user
            document_file.save()
        except Exception as exception:
            logger.error(
                'Error creating new file for document: %s; %s', self,
                exception, exc_info=True
            )
            raise
        else:
            logger.debug('New document file queued for document: %s', self)

            document_file.versions_new(
                action_name=action_name, comment=comment, user=user
            )

    def get_api_image_url(self, *args, **kwargs):
        version_active = self.version_active
        if version_active:
            return version_active.get_api_image_url(*args, **kwargs)
        else:
            raise AppImageError(
                error_name=IMAGE_ERROR_DOCUMENT_VERSION_ACTIVE_MISSING
            )

    def get_label(self):
        return self.label or gettext(
            message='Document stub, id: %d'
        ) % self.pk

    get_label.short_description = _(message='Label')

    def get_page_count(self, user):
        version_active = self.version_active
        if version_active:
            page_count = version_active.get_page_count(user=user)
            return page_count
        else:
            return 0
    get_page_count.short_description = _(message='Pages')

    @property
    def is_in_trash(self):
        return self.in_trash

    @property
    def pages(self):
        try:
            return self.version_active.pages
        except AttributeError:
            DocumentVersionPage = apps.get_model(
                app_label='documents', model_name='DocumentVersionPage'
            )

            return DocumentVersionPage.objects.none()
