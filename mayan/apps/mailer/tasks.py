import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from mayan.celery import app

from .literals import ERROR_LOG_DOMAIN_NAME

logger = logging.getLogger(name=__name__)


@app.task(ignore_result=True)
def task_send_object(
    content_type_id, body, object_id, sender, subject, recipient,
    mailing_profile_id, as_attachment=False, object_name=None,
    organization_installation_url=None, user_id=None
):
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )
    UserMailer = apps.get_model(
        app_label='mailer', model_name='UserMailer'
    )
    User = get_user_model()

    content_type = ContentType.objects.get_for_id(id=content_type_id)
    obj = content_type.get_object_for_this_type(pk=object_id)

    mailing_profile = UserMailer.objects.get(pk=mailing_profile_id)

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    try:
        mailing_profile.send_object(
            as_attachment=as_attachment, body=body, obj=obj,
            object_name=object_name,
            organization_installation_url=organization_installation_url,
            subject=subject, to=recipient, user=user
        )
    except Exception as exception:
        logger.error(
            'Error sending object to: %s using mailing profile id: %s; %s',
            recipient, mailing_profile_id, exception, exc_info=True
        )
        mailing_profile.error_log.create(
            domain_name=ERROR_LOG_DOMAIN_NAME,
            text='{}; {}'.format(
                exception.__class__.__name__, exception
            )
        )
        if settings.DEBUG:
            raise
