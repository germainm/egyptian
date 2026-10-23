from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from mayan.apps.organizations.utils import get_organization_installation_url
from mayan.apps.rest_api import generics
from mayan.apps.rest_api.api_view_mixins import ContentTypeAPIViewMixin

from .exceptions import MailerError
from .mailing_actions import ModelMailingAction
from .models import UserMailer
from .permissions import (
    permission_mailing_profile_create, permission_mailing_profile_delete,
    permission_mailing_profile_edit, permission_mailing_profile_view
)
from .serializers import (
    MailingProfileActionSerializer, MailingProfileSerializer
)
from .tasks import task_send_object


class APIMailingProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    delete: Delete the selected mailing profile.
    get: Return the details of the selected mailing profile.
    patch: Edit the selected mailing profile.
    put: Edit the selected mailing profile.
    """
    lookup_url_kwarg = 'mailing_profile_id'
    mayan_object_permission_map = {
        'DELETE': permission_mailing_profile_delete,
        'GET': permission_mailing_profile_view,
        'PATCH': permission_mailing_profile_edit,
        'PUT': permission_mailing_profile_edit
    }
    serializer_class = MailingProfileSerializer
    source_queryset = UserMailer.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIMailingProfileListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the mailing profiles.
    post: Create a new mailing profile.
    """
    mayan_object_permission_map = {'GET': permission_mailing_profile_view}
    mayan_view_permission_map = {'POST': permission_mailing_profile_create}
    serializer_class = MailingProfileSerializer
    source_queryset = UserMailer.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIMailObjectBaseView(
    ContentTypeAPIViewMixin, generics.ObjectActionAPIView
):
    lookup_url_kwarg = 'object_id'
    serializer_class = MailingProfileActionSerializer

    def get_as_attachment(self):
        model_mailing_action = self.get_model_mailing_action()

        as_attachment = model_mailing_action.as_attachment

        return as_attachment

    def get_mailing_action_name(self):
        raise NotImplementedError

    def get_mayan_object_permission_map(self):
        model_mailing_action = self.get_model_mailing_action()

        permission = model_mailing_action.kwargs['permission']

        return permission

    def get_model_mailing_action(self):
        action_name = self.get_mailing_action_name()
        content_type = self.get_content_type()
        model = content_type.model_class()

        try:
            model_mailing_action = ModelMailingAction.get_action_for_model(
                action_name=action_name, model=model
            )
        except MailerError as exception:
            raise ValidationError(
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [str(exception)]
                }, code='invalid'
            )
        else:
            return model_mailing_action

    def get_source_queryset(self):
        model_mailing_action = self.get_model_mailing_action()
        manager_name = model_mailing_action.kwargs['manager_name']
        model = self.get_content_type().model_class()

        manager = getattr(model, manager_name)

        return manager.all()

    def object_action(self, obj, request, serializer):
        as_attachment = self.get_as_attachment()
        mailing_profile = serializer.validated_data['mailing_profile']
        body = serializer.validated_data.get('body')
        content_type = self.get_content_type()
        model = content_type.model_class()
        object_name = model._meta.verbose_name
        organization_installation_url = get_organization_installation_url(
            request=self.request
        )
        recipient = serializer.validated_data['recipient']
        subject = serializer.validated_data.get('subject')

        kwargs = {
            'as_attachment': as_attachment,
            'body': body,
            'content_type_id': content_type.pk,
            'object_id': obj.pk,
            'object_name': object_name,
            'organization_installation_url': organization_installation_url,
            'recipient': recipient,
            'sender': self.request.user.email,
            'subject': subject,
            'mailing_profile_id': mailing_profile.pk,
            'user_id': self.request.user.pk
        }

        task_send_object.apply_async(kwargs=kwargs)


class APIMailObjectAttachmentView(APIMailObjectBaseView):
    """
    post: Send an object as attachment via email.
    """
    def get_mailing_action_name(self):
        return 'attachment'


class APIMailObjectLinkView(APIMailObjectBaseView):
    """
    post: Send an object link via email.
    """
    def get_mailing_action_name(self):
        return 'link'
