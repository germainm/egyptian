import json
import logging

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .classes import NullBackend

logger = logging.getLogger(__name__)


class QuotaBusinessModelMixin:
    def backend_label(self):
        return self.get_backend_instance().label
    backend_label.help_text = _(message='Driver used for this quota entry.')
    backend_label.short_description = _(message='Backend')

    def backend_filters(self):
        return self.get_backend_instance().filters()
    backend_filters.short_description = _(message='Arguments')

    def backend_usage(self):
        return self.get_backend_instance().usage()
    backend_usage.short_description = _(message='Usage')

    def dumps(self, data):
        self.backend_data = json.dumps(obj=data)
        self.save(
            update_fields=('backend_data',)
        )

    def get_backend_class(self):
        try:
            return import_string(dotted_path=self.backend_path)
        except ImportError as exception:
            logger.error(exception)

            return NullBackend

    def get_backend_instance(self):
        try:
            return self.get_backend_class()(
                **self.loads()
            )
        except Exception as exception:
            logger.error(exception, exc_info=True)

            return NullBackend()

    def loads(self):
        return json.loads(s=self.backend_data)
