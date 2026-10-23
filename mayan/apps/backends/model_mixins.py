import json
import logging

from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .literals import IMPORT_ERROR_EXCLUSION_TEXTS

logger = logging.getLogger(name=__name__)


class BackendModelMixin(models.Model):
    _backend_model_null_backend = None

    backend_path = models.CharField(
        max_length=128, help_text=_(
            message='The dotted Python path to the backend class.'
        ), verbose_name=_(message='Backend path')
    )
    backend_data = models.TextField(
        blank=True, help_text=_(
            message='JSON encoded data for the backend class.'
        ), verbose_name=_(message='Backend data')
    )

    class Meta:
        abstract = True

    def get_backend_class(self):
        try:
            return import_string(dotted_path=self.backend_path)
        except ModuleNotFoundError as exception:
            logger.error(
                'ModuleNotFoundError while importing backend: %s; %s',
                self.backend_path, exception
            )
            if self._backend_model_null_backend:
                return self._backend_model_null_backend
            else:
                raise
        except ImportError as exception:
            logger.error(
                'ImportError while importing backend: %s; %s',
                self.backend_path, exception
            )
            for import_error_exclusion_text in IMPORT_ERROR_EXCLUSION_TEXTS:
                if import_error_exclusion_text in str(exception):
                    raise

            if self._backend_model_null_backend:
                return self._backend_model_null_backend
            else:
                raise

    def get_backend_class_label(self):
        try:
            backend_class = self.get_backend_class()
        except ModuleNotFoundError as exception:
            return _(message='Error: `%s`') % exception

        return backend_class.label

    get_backend_class_label.short_description = _(message='Backend')
    get_backend_class_label.help_text = _(
        message='The backend class for this entry.'
    )

    def get_backend_data(self):
        backend_data = self.backend_data or '{}'
        return json.loads(s=backend_data)

    def set_backend_data(self, obj):
        self.backend_data = json.dumps(obj=obj)

    def get_backend_instance(self):
        backend_class = self.get_backend_class()

        kwargs = self.get_backend_data()

        return backend_class(model_instance_id=self.id, **kwargs)
