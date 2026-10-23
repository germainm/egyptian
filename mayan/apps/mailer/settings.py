from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_DOCUMENT_BODY_TEMPLATE, DEFAULT_DOCUMENT_SUBJECT_TEMPLATE,
    DEFAULT_LINK_BODY_TEMPLATE, DEFAULT_LINK_SUBJECT_TEMPLATE
)
from .setting_migrations import MailerSettingMigration

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Mailing'), migration_class=MailerSettingMigration,
    name='mailer', version='0002'
)

setting_attachment_subject_template = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_SUBJECT_TEMPLATE,
    global_name='MAILER_DOCUMENT_SUBJECT_TEMPLATE', help_text=_(
        message='Template for the document email form subject line.'
    )
)
setting_attachment_body_template = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_BODY_TEMPLATE,
    global_name='MAILER_DOCUMENT_BODY_TEMPLATE', help_text=_(
        message='Template for the document email form body text. '
        'Can include HTML.'
    )
)
setting_document_link_subject_template = setting_namespace.do_setting_add(
    default=DEFAULT_LINK_SUBJECT_TEMPLATE,
    global_name='MAILER_LINK_SUBJECT_TEMPLATE', help_text=_(
        message='Template for the document link email form subject line.'
    )
)
setting_document_link_body_template = setting_namespace.do_setting_add(
    default=DEFAULT_LINK_BODY_TEMPLATE,
    global_name='MAILER_LINK_BODY_TEMPLATE', help_text=_(
        message='Template for the document link email form body text. '
        'Can include HTML.'
    )
)
