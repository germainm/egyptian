import logging

from django.core.files.base import ContentFile
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _, gettext

logger = logging.getLogger(name=__name__)


class ModelMixinFileFieldOpen:
    def open(self, **kwargs):

        field_file = getattr(self, 'file')

        name = kwargs.pop('name', None)

        if name:
            logger.critical(
                'Caller specified an alternate filename "%s" for '
                'object: %s. Verify that this is not an attempt '
                'to access unauthorized files.', name, self
            )

        try:
            getattr(field_file.file, 'mode', None)
        except AttributeError:
            kwargs.pop('mode', None)

        name = field_file.name

        open_kwargs = {'name': name}

        open_kwargs.update(**kwargs)

        """
        The descriptor for the file attribute on the model instance. Return a
        FieldFile when accessed so you can write code like::

            >>> from myapp.models import MyModel
            >>> instance = MyModel.objects.get(pk=1)
            >>> instance.file.size

        Assign a file object on assignment so you can do::

            >>> with open('/path/to/hello.world', 'r') as f:
            ...     instance.file = File(f)
        """
        field_file.close()
        field_file.file.close()

        return self._open(**open_kwargs)


class DatabaseFileModelMixin(ModelMixinFileFieldOpen, models.Model):
    filename = models.CharField(
        db_index=True, max_length=255, verbose_name=_(message='Filename')
    )
    datetime = models.DateTimeField(
        auto_now_add=True, verbose_name=_(message='Date time')
    )

    class Meta:
        abstract = True

    def _open(self, **kwargs):
        return self.file.storage.open(**kwargs)

    def delete(self, *args, **kwargs):
        name = self.file.name
        self.file.close()

        if name:
            self.file.storage.delete(name=name)
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.file:
            self.file = ContentFile(
                content=b'', name=self.filename or gettext(
                    message='Unnamed file'
                )
            )

        self.filename = self.filename or str(self.file)
        super().save(*args, **kwargs)


class DownloadFileBusinessLogicMixin:
    def get_size_display(self):
        return filesizeformat(bytes_=self.file.size)

    get_size_display.short_description = _(message='Size')

    def get_user_display(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.user.username
    get_user_display.short_description = _(message='User')
