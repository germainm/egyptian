import logging

from django.utils.translation import gettext_lazy as _

from mayan.apps.document_states.classes import WorkflowAction

from mayan.apps.document_states.models.workflow_instance_models import (
    WorkflowInstance
)
from mayan.apps.user_management.querysets import get_user_queryset

from .models import Message

logger = logging.getLogger(name=__name__)


class WorkflowActionMessageSend(WorkflowAction):
    form_fields = {
        'group_name_list': {
            'label': _(message='Group name list'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Comma separated list of user group names '
                    'that will receive the message. Can be a static value or '
                    'a template.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        },
        'role_label_list': {
            'label': _(message='Role label list'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Comma separated list of role labels '
                    'that will receive the message. Can be a static value or '
                    'a template.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        },
        'username_list': {
            'label': _(message='Username list'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Comma separated list of usernames that will '
                    'receive the message. Can be a static value or '
                    'a template.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        },
        'subject': {
            'label': _(message='Subject'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Subject of the message to be sent. Can be a '
                    'static value or a template.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        },
        'body': {
            'label': _(message='Body'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='The actual text to send. Can be a static '
                    'value or a template.'
                ),
                'model': WorkflowInstance,
                'model_variable': 'workflow_instance',
                'required': True
            }
        }
    }
    label = _(message='Send user message')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Recipients'), {
                    'fields': (
                        'group_name_list', 'role_label_list', 'username_list'
                    )
                },
            ), (
                _(message='Content'), {
                    'fields': ('subject', 'body')
                }
            )
        )
        return fieldsets

    def execute(self, context):
        final_username_list = []
        queryset_users = get_user_queryset()


        group_name_list = self.render_field(
            field_name='group_name_list', context=context
        ) or ''
        group_name_list = group_name_list.split(',')

        if group_name_list:
            queyset_group_users = queryset_users.filter(
                groups__name__in=group_name_list
            )
            final_username_list.extend(
                queyset_group_users.values_list('username', flat=True)
            )


        role_label_list = self.render_field(
            field_name='role_label_list', context=context
        ) or ''
        role_label_list = role_label_list.split(',')

        if role_label_list:
            queyset_role_users = queryset_users.filter(
                groups__roles__label__in=role_label_list
            )
            final_username_list.extend(
                queyset_role_users.values_list('username', flat=True)
            )


        username_list = self.render_field(
            field_name='username_list', context=context
        ) or ''
        username_list = username_list.split(',')
        if username_list:
            final_username_list.extend(username_list)

        subject = self.render_field(
            field_name='subject', context=context
        ) or ''

        body = self.render_field(
            field_name='body', context=context
        ) or ''

        queryset_users_to_message = queryset_users.filter(
            username__in=final_username_list
        )

        for user in queryset_users_to_message:
            Message.objects.create(body=body, subject=subject, user=user)
