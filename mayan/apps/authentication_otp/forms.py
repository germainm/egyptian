import pyotp

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import mayan
from mayan.apps.authentication.forms import AuthenticationFormBase
from mayan.apps.authentication.literals import (
    SESSION_MULTI_FACTOR_USER_ID_KEY
)
from mayan.apps.converter.fields import QRCodeImageField
from mayan.apps.forms import form_fields, form_widgets, forms

from .models import UserOTPData


class AuthenticationFormTOTP(AuthenticationFormBase):
    error_messages = {
        'invalid_token': _(
            message='Token is either invalid or expired.'
        )
    }

    token = form_fields.CharField(
        label=_(message='TOTP token'), widget=form_widgets.TextInput(
            attrs={
                'autocomplete': 'one-time-code', 'autofocus': True,
                'inputmode': 'numeric'
            }
        )
    )

    @classmethod
    def condition(cls, authentication_backend, wizard):
        user_id = wizard.request.session.get(
            SESSION_MULTI_FACTOR_USER_ID_KEY, None
        )

        if user_id:
            user = get_user_model().objects.get(pk=user_id)
            kwargs = {
                'user__{}'.format(
                    authentication_backend.login_form_class.PASSWORD_FIELD
                ): user.username
            }

            try:
                otp_data = UserOTPData.objects.get(**kwargs)
            except UserOTPData.DoesNotExist:
                return False
            else:
                return otp_data.is_enabled()
        else:
            return False

    def clean(self):
        user_id = self.request.session.get(
            SESSION_MULTI_FACTOR_USER_ID_KEY, None
        )

        if user_id:
            user = get_user_model().objects.get(pk=user_id)
            self.user_cache = authenticate(
                factor_name='otp_token',
                otp_token=self.cleaned_data.get('token'),
                request=self.request, user=user
            )
            if self.user_cache is None:
                raise ValidationError(
                    code='invalid_token',
                    message=self.error_messages['invalid_token']
                )

        return self.cleaned_data


class FormUserOTPDataDetail(forms.DetailForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        extra_fields = ()

        otp_enabled = instance.otp_data.is_enabled()

        extra_fields = (
            {
                'label': _(message='OTP enabled?'),
                'func': lambda instance: _(message='Yes') if otp_enabled else _(message='No')
            },
        )

        kwargs['extra_fields'] = extra_fields
        super().__init__(*args, **kwargs)

    class Meta:
        fields = ()
        model = UserOTPData


class FormUserOTPDataEdit(forms.Form):
    qr_code = QRCodeImageField(disabled=True, label='', required=False)
    secret = form_fields.CharField(
        disabled=True,
        help_text=_(
            message='Scan the QR code or enter the secret in your '
            'authentication device. Do not share this secret, treat it like '
            'a password.'
        ), label=_(message='Secret'), required=False, widget=form_widgets.TextInput(
            attrs={'readonly': 'readonly'}
        )
    )
    signed_secret = form_fields.CharField(
        label=_(message='Secret'), required=False, widget=form_widgets.HiddenInput(
            attrs={'readonly': 'readonly'}
        )
    )
    token = form_fields.CharField(
        help_text=_(
            message='Enter the corresponding token to validate that the '
            'secret was saved correct.'
        ),
        label=_(message='Token'), widget=form_widgets.TextInput(
            attrs={
                'autocomplete': 'one-time-code', 'autofocus': True,
                'inputmode': 'numeric'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        secret = self.initial['secret']
        if secret:
            topt = pyotp.totp.TOTP(s=secret)
            url = topt.provisioning_uri(
                issuer_name=mayan.__title__, name=user.email
            )

            self.fields['qr_code'].initial = url

        self.fields['qr_code'].widget.attrs.update(
            {'style': 'margin:auto;'}
        )

    def clean_token(self):
        secret = self.cleaned_data['secret']
        token = self.cleaned_data['token']

        totp = pyotp.TOTP(secret)

        if token.strip() != totp.now():
            raise ValidationError(
                code='token_invalid',
                message=_(
                    message='Token is incorrect for the specified secret.'
                )
            )

        return token
