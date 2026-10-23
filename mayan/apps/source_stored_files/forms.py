import logging

from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets
from mayan.apps.sources.forms import UploadBaseForm

logger = logging.getLogger(name=__name__)


class StoredFileUploadForm(UploadBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.fields['stored_source_file_id'].choices = [
                (
                    stored_source_file.encoded_filename, str(
                        stored_source_file
                    )
                ) for stored_source_file in self.source.get_backend_instance().get_stored_file_list()
            ]
        except Exception as exception:
            logger.error('exception: %s', exception)

    stored_source_file_id = form_fields.ChoiceField(
        label=_(message='File'), widget=form_widgets.Select(
            attrs={'class': 'select2'}
        )
    )
