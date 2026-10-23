from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_widgets, forms

from .models import Tag
from .widgets import TagFormWidget


class TagForm(forms.ModelForm):
    class Meta:
        fields = ('label', 'color')
        model = Tag
        widgets = {
            'color': form_widgets.ColorWidget(
                auto_color_source_field_name='label'
            )
        }


class TagMultipleSelectionForm(forms.FilteredSelectionForm):
    class Media:
        js = ('tags/js/tags_form.js',)

    class Meta:
        allow_multiple = True
        field_name = 'tags'
        label = _(message='Tags')
        required = False
        widget_class = TagFormWidget
        widget_attributes = {'class': 'select2-tags'}
