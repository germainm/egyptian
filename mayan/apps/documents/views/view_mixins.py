class RecentDocumentViewMixin:
    recent_document_view_document_property_name = 'object'

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        getattr(
            self, self.recent_document_view_document_property_name
        ).add_as_recent_document_for_user(user=request.user)

        return result
