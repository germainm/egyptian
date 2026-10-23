from mayan.apps.common.serialization import yaml_dump
from mayan.apps.forms import form_widgets, forms

from .models import DocumentTypeDriverConfiguration


class FormDocumentTypeFileMetadataDriverConfiguration(forms.ModelForm):
    class Meta:
        fields = ('enabled', 'arguments')
        model = DocumentTypeDriverConfiguration

    def __init__(self, driver_configuration=None, *args, **kwargs):
        self._driver_configuration = driver_configuration

        super().__init__(*args, **kwargs)

        if self.instance:
            arguments = self.instance.get_arguments()

            for key, value in arguments.items():
                self.initial[key] = value

        self.fields['arguments'].widget = form_widgets.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()

        result = {}

        argument_name_list = self.instance.stored_driver.driver_class.get_argument_name_list()

        for argument_name in argument_name_list:
            value = cleaned_data.get(argument_name)
            if value is not None:
                result[argument_name] = value

        cleaned_data['arguments'] = yaml_dump(data=result)

        return cleaned_data
