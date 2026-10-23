class DocumentMetadataBusinessLogicMixin:
    @property
    def is_required(self):
        return self.metadata_type.get_required_for(
            document_type=self.document.document_type
        )
