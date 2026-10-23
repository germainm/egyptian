from django.shortcuts import reverse
from django.template import RequestContext
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.views.generics import MultipleObjectFormActionView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms import TagMultipleSelectionForm
from ..icons import (
    icon_document_tag_list, icon_document_tag_multiple_attach,
    icon_document_tag_multiple_remove

)
from ..links import link_document_tag_multiple_attach
from ..models import DocumentTag, Tag
from ..permissions import (
    permission_tag_attach, permission_tag_remove, permission_tag_view
)

from .tag_views import TagListView


class TagAttachActionView(MultipleObjectFormActionView):
    form_class = TagMultipleSelectionForm
    object_permission = permission_tag_attach
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_plural = _(
        message='Tags attached to %(count)d documents successfully.'
    )
    success_message_single = _(
        message='Tags attached to document "%(object)s" successfully.'
    )
    success_message_singular = _(
        message='Tags attached to %(count)d document successfully.'
    )
    title_plural = _(message='Attach tags to %(count)d documents.')
    title_single = _(message='Attach tags to document: %(object)s')
    title_singular = _(message='Attach tags to %(count)d document.')
    view_icon = icon_document_tag_multiple_attach

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Attach')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_form_extra_kwargs(self):
        kwargs = {
            'help_text': _(message='Tags to be attached.'),
            'permission': permission_tag_attach,
            'queryset': Tag.objects.all(),
            'user': self.request.user
        }

        if self.object_list.count() == 1:
            kwargs.update(
                {
                    'queryset': Tag.objects.exclude(
                        pk__in=self.object_list.first().tags.all()
                    )
                }
            )

        return kwargs

    def get_post_action_redirect(self):
        if self.object_list.count() == 1:
            return reverse(
                kwargs={
                    'document_id': self.object_list.first().pk
                }, viewname='tags:document_tag_list'
            )
        else:
            return super().get_post_action_redirect()

    def object_action(self, form, instance):
        for tag in form.cleaned_data['tags']:
            AccessControlList.objects.check_access(
                obj=tag, permission=permission_tag_attach,
                user=self.request.user
            )

            tag.attach_to(document=instance, user=self.request.user)


class DocumentTagListView(ExternalObjectViewMixin, TagListView):
    external_object_permission = permission_tag_view
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    tag_model = DocumentTag
    view_icon = icon_document_tag_list

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'hide_link': True,
                'no_results_main_link': link_document_tag_multiple_attach.resolve(
                    context=RequestContext(
                        dict_={'object': self.external_object},
                        request=self.request
                    )
                ),
                'no_results_title': _(
                    message='Document has no tags attached'
                ),
                'object': self.external_object,
                'title': _(
                    message='Tags for document: %s'
                ) % self.external_object
            }
        )
        return context

    def get_tag_queryset(self):
        return self.external_object.get_tags(
            permission=permission_tag_view, user=self.request.user
        )


class TagRemoveActionView(MultipleObjectFormActionView):
    form_class = TagMultipleSelectionForm
    object_permission = permission_tag_remove
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_plural = _(
        message='Tags removed from %(count)d documents successfully.'
    )
    success_message_single = _(
        message='Tags removed from document "%(object)s" successfully.'
    )
    success_message_singular = _(
        message='Tags removed from %(count)d document successfully.'
    )
    title_plural = _(message='Remove tags from %(count)d documents.')
    title_single = _(message='Remove tags from document: %(object)s')
    title_singular = _(message='Remove tags from %(count)d document.')
    view_icon = icon_document_tag_multiple_remove

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Remove')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_form_extra_kwargs(self):
        kwargs = {
            'help_text': _(message='Tags to be removed.'),
            'permission': permission_tag_remove,
            'queryset': Tag.objects.all(),
            'user': self.request.user
        }

        if self.object_list.count() == 1:
            kwargs.update(
                {
                    'queryset': self.object_list.first().tags.all()
                }
            )

        return kwargs

    def get_post_action_redirect(self):
        if self.object_list.count() == 1:
            return reverse(
                kwargs={
                    'document_id': self.object_list.first().pk
                }, viewname='tags:document_tag_list'
            )
        else:
            return super().get_post_action_redirect()

    def object_action(self, form, instance):
        for tag in form.cleaned_data['tags']:
            AccessControlList.objects.check_access(
                obj=tag, permission=permission_tag_remove,
                user=self.request.user
            )

            tag.remove_from(document=instance, user=self.request.user)
