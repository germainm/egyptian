try:
    from allauth.account.adapter import DefaultAccountAdapter
except ImportError:
    print('ERROR: This authentication adapter requires django-allauth.')
    raise

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .literals import ADMIN_EMAIL_ADDRESSES


class AutoadminAccountAdapter(DefaultAccountAdapter):

    def confirm_email(self, request, email_address):
        super().confirm_email(request=request, email_address=email_address)

        if email_address.email in ADMIN_EMAIL_ADDRESSES:
            user = email_address.user
            user.is_staff = user.is_superuser = True
            user.save()

            messages.info(
                request=request, message=_(
                    message='Welcome Admin! You have been given super user '
                    'privileges. Use them with caution.'
                )
            )
