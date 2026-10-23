import yaml

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_dump, yaml_load
from mayan.apps.forms import form_fields, form_widgets, forms

from .fields import ImageField
from .models import Asset, LayerTransformation
from .transformations import BaseTransformation


class AssetDetailForm(forms.DetailForm):
    preview = ImageField(
        image_alt_text=_(message='Asset preview image'), label=_(
            message='Preview'
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preview'].initial = kwargs['instance']

    class Meta:
        fields = ('label', 'internal_name', 'preview')
        model = Asset


class LayerTransformationSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        layer = kwargs.pop('layer')
        super().__init__(*args, **kwargs)
        self.fields[
            'transformation'
        ].choices = BaseTransformation.get_transformation_choices(
            layer=layer
        )

    transformation = form_fields.ChoiceField(
        choices=(), help_text=_(
            message='Available transformations for this layer.'
        ), label=_(message='Transformation')
    )


class LayerTransformationForm(forms.ModelForm):
    class Meta:
        fields = ('arguments', 'order')
        model = LayerTransformation

    def __init__(self, *args, **kwargs):
        self._transformation_name = kwargs.pop('transformation_name', None)

        super().__init__(*args, **kwargs)
        transformation_class = self.get_transformation_class()
        if self.instance:
            try:
                obj = yaml_load(stream=self.instance.arguments or '{}')
            except Exception:
                obj = {}

            for key, value in obj.items():
                self.initial[key] = value

        self.transformation_template_name = transformation_class.get_template_name()

        if self.transformation_template_name:
            self.fields['arguments'].widget.attrs['class'] = 'd-none'
            self.fields['order'].widget.attrs['class'] = 'd-none'
        else:
            self.fields['arguments'].widget = form_widgets.HiddenInput()

    def get_transformation_class(self):
        if not self._transformation_name:
            return self.instance.get_transformation_class()
        else:
            return BaseTransformation.get(name=self._transformation_name)

    def clean(self):
        if self.transformation_template_name:
            try:
                arguments = yaml_load(
                    stream=self.cleaned_data['arguments']
                )
            except yaml.YAMLError:
                raise ValidationError(
                    message=_(
                        message='"%s" not a valid entry.'
                    ) % self.cleaned_data['arguments']
                )

            if isinstance(arguments, dict):
                self.get_transformation_class().validate_arguments(
                    arguments=arguments
                )
        else:
            arguments = {}

            for argument in self.get_transformation_class().get_arguments():
                if self.cleaned_data[argument] is not None:
                    arguments[argument] = self.cleaned_data[argument]

            self.get_transformation_class().validate_arguments(
                arguments=arguments
            )

            self.cleaned_data['arguments'] = yaml_dump(data=arguments)
