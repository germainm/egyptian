from furl import furl

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.views.generics import (
    MultipleObjectFormActionView, SingleObjectListView
)
from mayan.apps.views.utils import convert_to_id_list
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms import (
    DocumentMetadataAddForm, DocumentMetadataFormSet,
    DocumentMetadataRemoveFormSet
)
from ..icons import (
    icon_document_metadata_add, icon_document_metadata_edit,
    icon_document_metadata_list, icon_document_metadata_remove, icon_metadata
)
from ..links import link_metadata_add, link_metadata_multiple_add
from ..mixins import DocumentMetadataSameTypeViewMixin
from ..models.metadata_instance_models import DocumentMetadata
from ..models.metadata_type_models import MetadataType
from ..permissions import (
    permission_document_metadata_add, permission_document_metadata_edit,
    permission_document_metadata_remove, permission_document_metadata_view
)
from ..utils import save_metadata_list


class DocumentMetadataAddView(
    DocumentMetadataSameTypeViewMixin, MultipleObjectFormActionView
):
    form_class = DocumentMetadataAddForm
    object_permission = permission_document_metadata_add
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='Metadata add request performed on %(count)d document'
    )
    success_message_plural = _(
        message='Metadata add request performed on %(count)d documents'
    )
    view_icon = icon_document_metadata_add

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'submit_label': _(message='Add'),
            'title': ngettext(
                singular='Add metadata types to document',
                plural='Add metadata types to documents',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Add metadata types to document: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_form_extra_kwargs(self):
        queryset = self.object_list

        result = {}

        if queryset.count():
            result.update(
                {
                    'document_type': queryset.first().document_type
                }
            )

        if queryset.count() == 1:
            result.update(
                {
                    'queryset': MetadataType.objects.get_for_document_type(
                        document_type=queryset.first().document_type
                    ).exclude(
                        pk__in=MetadataType.objects.get_for_document(
                            document=queryset.first()
                        )
                    )
                }
            )

        return result

    def get_post_object_action_url(self):
        if self.action_count == 1:
            return reverse(
                kwargs={
                    'document_id': self.action_id_list[0]
                }, viewname='metadata:metadata_edit'
            )
        elif self.action_count > 1:
            url = furl(
                args={
                    'id_list': convert_to_id_list(items=self.action_id_list)
                }, path=reverse(
                    viewname='metadata:metadata_multiple_edit'
                )
            )

            return url.tostr()

    def object_action(self, form, instance):
        queryset = AccessControlList.objects.restrict_queryset(
            queryset=form.cleaned_data['metadata_type'],
            permission=permission_document_metadata_add,
            user=self.request.user
        )

        for metadata_type in queryset:
            try:
                created = False
                try:
                    DocumentMetadata.objects.get(
                        document=instance,
                        metadata_type=metadata_type
                    )
                except DocumentMetadata.DoesNotExist:
                    document_metadata = DocumentMetadata(
                        document=instance,
                        metadata_type=metadata_type
                    )
                    document_metadata._event_actor = self.request.user
                    document_metadata.save()
                    created = True
            except Exception as exception:
                messages.error(
                    message=_(
                        message='Error adding metadata type '
                        '"%(metadata_type)s" to document: '
                        '%(document)s; %(exception)s'
                    ) % {
                        'document': instance,
                        'exception': ', '.join(
                            getattr(
                                exception, 'messages', (
                                    str(exception),
                                )
                            )
                        ),
                        'metadata_type': metadata_type
                    }, request=self.request
                )
            else:
                if created:
                    messages.success(
                        message=_(
                            message='Metadata type: %(metadata_type)s '
                            'successfully added to document %(document)s.'
                        ) % {
                            'document': instance,
                            'metadata_type': metadata_type
                        }, request=self.request
                    )
                else:
                    messages.warning(
                        message=_(
                            message='Metadata type: %(metadata_type)s '
                            'already present in document %(document)s.'
                        ) % {
                            'document': instance,
                            'metadata_type': metadata_type
                        }, request=self.request
                    )


class DocumentMetadataEditView(
    DocumentMetadataSameTypeViewMixin, MultipleObjectFormActionView
):
    form_class = DocumentMetadataFormSet
    object_permission = permission_document_metadata_edit
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='Metadata edit request performed on %(count)d document'
    )
    success_message_plural = _(
        message='Metadata edit request performed on %(count)d documents'
    )
    view_icon = icon_document_metadata_edit

    def get_extra_context(self):
        queryset = self.object_list

        id_list = ','.join(
            map(
                str, queryset.values_list('pk', flat=True)
            )
        )

        if queryset.count() == 1:
            no_results_main_link = link_metadata_add.resolve(
                context=RequestContext(
                    dict_={
                        'object': queryset.first()
                    },
                    request=self.request
                )
            )
        else:
            no_results_main_link = link_metadata_multiple_add.resolve(
                context=RequestContext(request=self.request)
            )
            no_results_main_link.url = '{}?id_list={}'.format(
                no_results_main_link.url, id_list
            )

        result = {
            'form_display_mode_table': True,
            'no_results_icon': icon_metadata,
            'no_results_main_link': no_results_main_link,
            'no_results_text': _(
                message='Add metadata types available for this document\'s '
                'type and assign them corresponding values.'
            ),
            'no_results_title': _(message='There is no metadata to edit'),
            'submit_label': _(message='Save'),
            'title': ngettext(
                singular='Edit document metadata',
                plural='Edit documents metadata',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Edit metadata for document: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_initial(self):
        queryset = self.object_list

        metadata_dict = {}
        initial = []

        for document in queryset:
            queryset_document_metadata = AccessControlList.objects.restrict_queryset(
                queryset=document.metadata.all(),
                permission=permission_document_metadata_edit,
                user=self.request.user
            )
            for document_metadata in queryset_document_metadata:
                metadata_dict.setdefault(
                    document_metadata.metadata_type, set()
                )

                if document_metadata.value:
                    metadata_dict[
                        document_metadata.metadata_type
                    ].add(document_metadata.value)

        for key, value in metadata_dict.items():
            initial.append(
                {
                    'document_type': document.document_type,
                    'metadata_type': key,
                    'value': ', '.join(value) if value else '',
                    'value_existing': ', '.join(value) if value else ''
                }
            )

        return initial

    def get_post_object_action_url(self):
        if self.action_count == 1:
            return reverse(
                kwargs={
                    'document_id': self.action_id_list[0]
                }, viewname='metadata:metadata_list'
            )
        elif self.action_count > 1:
            url = furl(
                args={
                    'id_list': convert_to_id_list(items=self.action_id_list)
                }, path=reverse(viewname='metadata:metadata_multiple_edit')
            )
            return url.tostr()

    def object_action(self, form, instance):
        queryset_document_metadata = AccessControlList.objects.restrict_queryset(
            queryset=instance.metadata.all(),
            permission=permission_document_metadata_edit,
            user=self.request.user
        )

        errors = []
        for form in form.forms:
            if form.cleaned_data['update']:
                if queryset_document_metadata.filter(metadata_type=form.cleaned_data['metadata_type_id']).exists():
                    try:
                        save_metadata_list(
                            document=instance,
                            metadata_list=[form.cleaned_data],
                            user=self.request.user
                        )
                    except Exception as exception:
                        errors.append(exception)

                        if settings.DEBUG or settings.TESTING:
                            raise

        for error in errors:
            if isinstance(error, ValidationError):
                exception_message = ', '.join(error.messages)
            else:
                exception_message = str(error)

            messages.error(
                message=_(
                    message='Error editing metadata for document: '
                    '%(document)s; %(exception)s.'
                ) % {
                    'document': instance,
                    'exception': exception_message
                }, request=self.request
            )

            if settings.DEBUG or settings.TESTING:
                raise error
        else:
            messages.success(
                message=_(
                    message='Metadata for document %s edited successfully.'
                ) % instance, request=self.request
            )


class DocumentMetadataListView(ExternalObjectViewMixin, SingleObjectListView):
    external_object_permission = permission_document_metadata_view
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    object_permission = permission_document_metadata_view
    view_icon = icon_document_metadata_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'object': self.external_object,
            'no_results_icon': icon_metadata,
            'no_results_main_link': link_metadata_add.resolve(
                context=RequestContext(
                    dict_={'object': self.external_object},
                    request=self.request
                )
            ),
            'no_results_text': _(
                message='Add metadata types this document\'s type to be '
                'able to add them to individual documents. Once added to '
                'individual document, you can then edit their values.'
            ),
            'no_results_title': _(
                message='This document doesn\'t have any metadata'
            ),
            'title': _(
                message='Metadata for document: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.metadata.all()


class DocumentMetadataRemoveView(
    DocumentMetadataSameTypeViewMixin, MultipleObjectFormActionView
):
    form_class = DocumentMetadataRemoveFormSet
    object_permission = permission_document_metadata_remove
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='Metadata remove request performed on %(count)d document'
    )
    success_message_plural = _(
        message='Metadata remove request performed on %(count)d documents'
    )
    view_icon = icon_document_metadata_remove

    def get_extra_context(self):
        queryset = self.object_list

        result = {
            'form_display_mode_table': True,
            'submit_label': _(message='Remove'),
            'title': ngettext(
                singular='Remove metadata types from the document',
                plural='Remove metadata types from the documents',
                number=queryset.count()
            )
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        message='Remove metadata types from the document: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_initial(self):
        queryset = self.object_list

        metadata = {}
        for document in queryset:
            queryset_document_metadata = AccessControlList.objects.restrict_queryset(
                queryset=document.metadata.all(),
                permission=permission_document_metadata_remove,
                user=self.request.user
            )

            for document_metadata in queryset_document_metadata:
                value = document_metadata.value or ''
                if document_metadata.metadata_type in metadata:
                    if value not in metadata[document_metadata.metadata_type]:
                        metadata[document_metadata.metadata_type].append(value)
                else:
                    metadata[document_metadata.metadata_type] = [value] if value else ''

        initial = []
        for key, value in metadata.items():
            initial.append(
                {
                    'document_type': queryset.first().document_type,
                    'metadata_type': key,
                    'value': ', '.join(value)
                }
            )
        return initial

    def get_post_object_action_url(self):
        if self.action_count == 1:
            return reverse(
                kwargs={
                    'document_id': self.action_id_list[0]
                }, viewname='metadata:metadata_list'
            )

    def object_action(self, form, instance):
        for form in form.forms:
            if form.cleaned_data['update']:
                queryset = AccessControlList.objects.restrict_queryset(
                    queryset=MetadataType.objects.all(),
                    permission=permission_document_metadata_remove,
                    user=self.request.user
                )
                metadata_type = get_object_or_404(
                    klass=queryset, pk=form.cleaned_data['metadata_type_id']
                )
                try:
                    document_metadata = DocumentMetadata.objects.get(
                        document=instance, metadata_type=metadata_type
                    )
                    document_metadata._event_actor = self.request.user
                    document_metadata.delete()
                    messages.success(
                        message=_(
                            message='Successfully remove metadata type '
                            '"%(metadata_type)s" from document: %(document)s.'
                        ) % {
                            'document': instance,
                            'metadata_type': metadata_type
                        }, request=self.request
                    )
                except ValidationError as exception:
                    messages.error(
                        message=_(
                            message='Error removing metadata type '
                            '"%(metadata_type)s" from document: '
                            '%(document)s; %(exception)s'
                        ) % {
                            'document': instance,
                            'exception': ', '.join(exception.messages),
                            'metadata_type': metadata_type
                        }, request=self.request
                    )
