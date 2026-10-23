from django.http import Http404


class ViewMixinURLBackend:
    def get_backend_class(self):
        try:
            return self.backend_class.get(
                name=self.kwargs['backend_path']
            )
        except KeyError:
            raise Http404(
                '{} class not found'.format(
                    self.kwargs['backend_path']
                )
            )


class ViewMixinDynamicFormBackendClass:
    def get_form_schema(self):
        backend_class = self.get_backend_class()

        form_schema = backend_class.get_form_schema(
            **self.get_form_schema_extra_kwargs()
        )

        return form_schema

    def get_form_schema_extra_kwargs(self):
        return {}
