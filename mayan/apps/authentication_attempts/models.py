from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.templating.template_backends import Template

from .literals import (
    LOGIN_ATTEMPT_RESULT_CHOICES, LOGIN_ATTEMPT_SOURCE_CHOICES,
    LOGIN_ATTEMPT_SOURCE_SESSION
)
from .managers import LoginAttemptManager
from .model_mixins import LoginAttemptBusinessLogicMixin


class LoginAttempt(LoginAttemptBusinessLogicMixin, models.Model):
    _ordering_fields = ('datetime',)

    username = models.CharField(
        db_index=True, help_text=_(
            message='The username exactly as it was supplied for the '
            'authentication attempt. For failed attempts this may not '
            'match any existing account.'
        ), max_length=254, verbose_name=_(message='Username')
    )
    user = models.ForeignKey(
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_(
            message='The existing account that the supplied username '
            'resolved to, if any.'
        ), related_name='login_attempts', to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )
    result = models.CharField(
        choices=LOGIN_ATTEMPT_RESULT_CHOICES, db_index=True,
        help_text=_(
            message='Whether the authentication attempt succeeded or failed.'
        ), max_length=32, verbose_name=_(message='Result')
    )
    source = models.CharField(
        choices=LOGIN_ATTEMPT_SOURCE_CHOICES,
        default=LOGIN_ATTEMPT_SOURCE_SESSION,
        help_text=_(
            message='The subsystem through which the authentication was '
            'attempted, such as the interactive session or the API.'
        ), max_length=32, verbose_name=_(message='Source')
    )
    ip_address = models.GenericIPAddressField(
        blank=True, help_text=_(
            message='The client address as resolved by the lockout '
            'layer. Behind a reverse proxy this is only meaningful when '
            'the proxy trust is configured; treat it as best effort.'
        ), null=True, verbose_name=_(message='IP address')
    )
    user_agent = models.TextField(
        blank=True, help_text=_(
            message='Information about the web browser or application '
            'used to make the login attempt.'
        ), verbose_name=_(message='User agent')
    )
    datetime = models.DateTimeField(
        auto_now_add=True, db_index=True,
        verbose_name=_(message='Date and time')
    )

    objects = LoginAttemptManager()

    class Meta:
        ordering = ('-datetime',)
        verbose_name = _(message='Login attempt')
        verbose_name_plural = _(message='Login attempts')

    def __str__(self):
        template = Template(
            template_string='{{ datetime }} - {{ user }} - {{ result }}'
        )

        result = template.render(
            context={
                'datetime': self.datetime,
                'user': self.user,
                'result': self.get_result_display()
            }
        )

        return result
