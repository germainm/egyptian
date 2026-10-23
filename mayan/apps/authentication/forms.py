from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, forms
from mayan.apps.user_management.querysets import get_user_queryset

from .classes import AuthenticationBackend
from .permissions import permission_users_impersonate


class AuthenticationFormBase(forms.Form):
    _label = None
    PASSWORD_FIELD = 'username'

    def __init__(
        self, data, files, prefix, initial, request=None, wizard=None
    ):
        self.request = request
        self.user_cache = None
        self.wizard = wizard

        super().__init__(
            data=data, files=files, prefix=prefix, initial=initial
        )

    def get_user(self):
        return self.user_cache


class AuthenticationFormMixinMayanBackend:
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            authentication_backend = AuthenticationBackend.cls_get_instance()
            self.user_cache = authentication_backend.authenticate(
                password=password, request=self.request, username=username
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(user=self.user_cache)

        return self.cleaned_data


class AuthenticationFormMixinRememberMe(forms.Form):
    _form_field_name_remember_me = 'remember_me'
    remember_me = form_fields.BooleanField(
        label=_(message='Remember me'), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_order = [
            field for field in self.fields if field != self._form_field_name_remember_me
        ]
        field_order.append(self._form_field_name_remember_me)

        self.order_fields(field_order=field_order)


class AuthenticationFormEmailPassword(
    AuthenticationFormMixinMayanBackend, AuthenticationFormMixinRememberMe,
    AuthenticationForm
):
    PASSWORD_FIELD = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        UserModel = get_user_model()

        self.username_field = UserModel._meta.get_field(field_name='email')
        username_max_length = self.username_field.max_length or 254
        self.fields['username'].max_length = username_max_length
        self.fields['username'].widget.attrs['maxlength'] = username_max_length
        self.fields['username'].label = self.username_field.verbose_name


class AuthenticationFormUsernamePassword(
    AuthenticationFormMixinMayanBackend, AuthenticationFormMixinRememberMe,
    AuthenticationForm
):
    PASSWORD_FIELD = 'username'


class UserImpersonationOptionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permanent'] = form_fields.BooleanField(
            label=_(message='Permanent'), help_text=_(
                message='If selected, disables ending impersonation.'
            ), required=False
        )


class UserImpersonationSelectionForm(
    forms.FilteredSelectionForm, UserImpersonationOptionsForm
):
    class Meta:
        allow_multiple = False
        field_name = 'user_to_impersonate'
        label = _(message='User')
        queryset = get_user_queryset().none()
        permission = permission_users_impersonate
        required = True
        widget_attributes = {'class': 'select2'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = get_user_queryset().exclude(
            pk=kwargs['user'].pk
        )
        self.fields['user_to_impersonate'].queryset = queryset
        self.order_fields(
            field_order=('user_to_impersonate', 'permanent')
        )
