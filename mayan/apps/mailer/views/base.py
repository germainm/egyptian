from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.acls.models import AccessControlList
from mayan.apps.organizations.utils import get_organization_installation_url
from mayan.apps.views.generics import MultipleObjectFormActionView

from ..exceptions import MailerError
from ..forms import ObjectMailForm
from ..mailing_actions import ModelMailingAction
from ..models import UserMailer
from ..permissions import permission_mailing_profile_use
from ..tasks import task_send_object


class MailingObjectSendView(MultipleObjectFormActionView):
    form_class = ObjectMailForm

    def get_as_attachment(self):
        model_mailing_action = self.get_model_mailing_action()

        as_attachment = model_mailing_action.as_attachment

        return as_attachment

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'submit_label': _(message='Send'),
            'title': ngettext(
                singular=self.title,
                plural=self.title_plural,
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message=self.title_document
                    ) % queryset.first()
                }
            )

        return result

    def get_form_extra_kwargs(self):
        return {
            'as_attachment': self.get_as_attachment(),
            'user': self.request.user
        }

    def get_mailing_action_name(self):
        raise NotImplementedError

    def get_model_mailing_action(self):
        action_name = self.get_mailing_action_name()
        model = self.source_queryset.model

        try:
            model_mailing_action = ModelMailingAction.get_action_for_model(
                action_name=action_name, model=model
            )
        except MailerError as exception:
            raise ValidationError(
                message=str(exception)
            )
        else:
            return model_mailing_action

    def get_object_permission(self):
        model_mailing_action = self.get_model_mailing_action()

        permission = model_mailing_action.kwargs['permission']

        return permission

    def object_action(self, form, instance):
        as_attachment = self.get_as_attachment()

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_mailing_profile_use,
            queryset=UserMailer.objects.filter(enabled=True),
            user=self.request.user
        )

        mailing_profile = get_object_or_404(
            klass=queryset, pk=form.cleaned_data['mailing_profile'].pk
        )

        content_type = ContentType.objects.get_for_model(model=instance)

        organization_installation_url = get_organization_installation_url(
            request=self.request
        )

        try:
            object_name = instance._meta.model._meta.verbose_name
        except AttributeError:
            object_name = _(message='Object')

        kwargs = {
            'as_attachment': as_attachment,
            'body': form.cleaned_data['body'],
            'content_type_id': content_type.pk,
            'object_id': instance.pk,
            'object_name': object_name,
            'organization_installation_url': organization_installation_url,
            'recipient': form.cleaned_data['email'],
            'sender': self.request.user.email,
            'subject': form.cleaned_data['subject'],
            'mailing_profile_id': mailing_profile.pk,
            'user_id': self.request.user.pk
        }

        task_send_object.apply_async(kwargs=kwargs)


class MailingObjectAttachmentSendView(MailingObjectSendView):
    def get_mailing_action_name(self):
        return 'attachment'


class MailingObjectLinkSendView(MailingObjectSendView):
    def get_mailing_action_name(self):
        return 'link'
