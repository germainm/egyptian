from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.sources.classes import DocumentCreateWizardStep
from mayan.apps.sources.wizard_steps import (
    DocumentCreateWizardStepDocumentType
)

from .forms import DocumentMetadataFormSet
from .models.metadata_type_models import MetadataType
from .permissions import permission_document_metadata_add
from .utils import decode_metadata_from_query_string, save_metadata_list


class DocumentCreateWizardStepMetadata(DocumentCreateWizardStep):
    form_class = DocumentMetadataFormSet
    label = _(message='Enter document metadata')
    name = 'metadata_entry'
    number = 1

    @staticmethod
    def get_metadata_queryset_for_document(document, user=None):
        queryset_documents = Document.valid.all()

        if user:
            queryset_documents = AccessControlList.objects.restrict_queryset(
                permission=permission_document_metadata_add,
                queryset=queryset_documents, user=user
            )

        try:
            queryset_documents.get(pk=document.pk)
        except Document.DoesNotExist:
            queryset_metadata_types = MetadataType.objects.none()
        else:
            queryset_metadata_types = MetadataType.objects.all()

            if user:
                queryset_metadata_types = AccessControlList.objects.restrict_queryset(
                    permission=permission_document_metadata_add,
                    queryset=queryset_metadata_types,
                    user=user
                )

        return queryset_metadata_types

    @staticmethod
    def get_metadata_queryset_for_document_type(document_type, user):
        queryset_document_types = DocumentType.objects.all()

        queryset_document_types_restricted = AccessControlList.objects.restrict_queryset(
            permission=permission_document_metadata_add,
            queryset=queryset_document_types, user=user
        )

        try:
            queryset_document_types_restricted.get(pk=document_type.pk)
        except DocumentType.DoesNotExist:
            queryset_metadata_types = MetadataType.objects.none()
        else:
            queryset_metadata_types = MetadataType.objects.filter(
                document_types__document_type=document_type.pk
            )

            queryset_metadata_types = AccessControlList.objects.restrict_queryset(
                permission=permission_document_metadata_add,
                queryset=queryset_metadata_types, user=user
            )

        return queryset_metadata_types

    @classmethod
    def condition(cls, wizard):
        cleaned_data = wizard.get_cleaned_data_for_step(
            step=DocumentCreateWizardStepDocumentType.name
        ) or {}

        document_type = cleaned_data.get('document_type')

        if document_type:
            return document_type.metadata.exists()

    @classmethod
    def get_form_initial(cls, wizard):
        initial = []

        step_data = wizard.get_cleaned_data_for_step(
            step=DocumentCreateWizardStepDocumentType.name
        )

        user = wizard.request.user

        if step_data:
            document_type = step_data['document_type']

            queryset_metadata_types = DocumentCreateWizardStepMetadata.get_metadata_queryset_for_document_type(
                document_type=document_type, user=user
            )

            for metadata_type in queryset_metadata_types:
                initial.append(
                    {
                        'document_type': document_type,
                        'metadata_type': metadata_type
                    }
                )

        return initial

    @classmethod
    def done(cls, wizard):
        result = {}
        try:
            cleaned_data = wizard.get_cleaned_data_for_step(step=cls.name)
        except KeyError:
            return result
        else:
            if cleaned_data:
                for index, metadata_entry in enumerate(iterable=cleaned_data):
                    if metadata_entry.get('update'):
                        result[
                            'metadata{}_metadata_type_id'.format(index)
                        ] = metadata_entry['metadata_type_id']
                        result[
                            'metadata{}_value'.format(index)
                        ] = metadata_entry['value']

            return result

    @classmethod
    def step_post_upload_process(
        cls, document, query_string, source_id, user_id
    ):
        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None

        if user:
            queryset_metadata_types_restricted = DocumentCreateWizardStepMetadata.get_metadata_queryset_for_document(
                document=document, user=user
            )

            metadata_dict_list = decode_metadata_from_query_string(
                query_string=query_string
            )

            queryset_metadata_types_restricted = queryset_metadata_types_restricted.filter(
                document_types__document_type=document.document_type.pk
            )


            metadata_dict_list_restricted = []

            metadata_type_id_list_restricted = queryset_metadata_types_restricted.values_list(
                'id', flat=True
            )

            for metadata_entry in metadata_dict_list:
                if int(metadata_entry['metadata_type_id']) in metadata_type_id_list_restricted:
                    metadata_dict_list_restricted.append(metadata_entry)

            save_metadata_list(
                create=True, document=document,
                metadata_list=metadata_dict_list_restricted, user=user
            )

    @classmethod
    def get_next_is_enabled(cls, wizard):
        step_data = wizard.get_cleaned_data_for_step(
            step=DocumentCreateWizardStepDocumentType.name
        )

        user = wizard.request.user

        if step_data:
            document_type = step_data['document_type']

            queryset_metadata_types = cls.get_metadata_queryset_for_document_type(
                document_type=document_type, user=user
            )

            queryset_metadata_types_required = MetadataType.objects.get_for_document_type(
                document_type=document_type, required=True
            )

            has_required_metadata = not queryset_metadata_types_required.exclude(
                pk__in=queryset_metadata_types.values('pk')
            ).exists()

            if not has_required_metadata:
                messages.error(
                    message=_(
                        message='One of more metadata types that are '
                        'required for this document type are not available.'
                    ), request=wizard.request
                )
                wizard.render_goto_step(goto_step=0)

                return False

        return True


DocumentCreateWizardStep.register(step=DocumentCreateWizardStepMetadata)
