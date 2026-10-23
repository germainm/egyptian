from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.forms import forms
from mayan.apps.templating.fields import ModelTemplateField

from ..forms import FormDocumentTypeFileMetadataDriverConfiguration


class ViewMixinDynamicConfigurationFormClass:
    def get_form_class(self):
        FormDriverArguments = self.object.stored_driver.driver_class.get_form_class()

        if not FormDriverArguments:
            obj = self.object

            argument_values_from_settings = obj.stored_driver.driver_class.get_argument_values_from_settings()

            class FormDriverArguments(forms.Form):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    argument_name_list = obj.stored_driver.driver_class.get_argument_name_list()

                    for argument_name in argument_name_list:
                        default_value = argument_values_from_settings.get(
                            argument_name
                        )

                        self.fields[argument_name] = ModelTemplateField(
                            initial_help_text=_(
                                message='The template string to be '
                                'evaluated. Leave empty to use the driver\'s '
                                'value passed via settings. Default '
                                'value: %s.'
                            ) % default_value, model=DocumentFile,
                            model_variable='document_file', required=False
                        )

        class FormDriverArgumentsMerged(
            FormDriverArguments,
            FormDocumentTypeFileMetadataDriverConfiguration
        ):
            view = self

        return FormDriverArgumentsMerged
