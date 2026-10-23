import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from mayan.celery import app

from .classes import DocumentVersionExporter
from .literals import ERROR_LOG_DOMAIN_NAME

logger = logging.getLogger(name=__name__)


@app.task(ignore_result=True)
def task_document_version_export(
    document_version_id, organization_installation_url=None, user_id=None
):
    DocumentVersion = apps.get_model(
        app_label='documents', model_name='DocumentVersion'
    )
    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    document_version = DocumentVersion.objects.get(
        pk=document_version_id
    )

    document_version_exporter = DocumentVersionExporter(document_version=document_version)

    try:
        document_version_exporter.export_to_download_file(
            organization_installation_url=organization_installation_url,
            user=user
        )
    except Exception as exception:
        logger.error(
            'Error exporting document version id: %s; %s',
            document_version_id, exception, exc_info=True
        )
        document_version.error_log.create(
            domain_name=ERROR_LOG_DOMAIN_NAME,
            text='{}; {}'.format(
                exception.__class__.__name__, exception
            )
        )
        if settings.DEBUG:
            raise
