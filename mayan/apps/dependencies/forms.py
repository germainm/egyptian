from mayan.apps.forms import form_fields, form_widgets, forms

from .classes import Dependency


class DependenciesLicensesForm(forms.Form):
    text = form_fields.CharField(
        label='',
        widget=form_widgets.TextAreaDiv(
            attrs={
                'class': 'scrollable'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_legal_list = []

        for dependency in Dependency.get_all():
            text_legal = dependency.get_legal_text()
            if text_legal:
                text_legal_list.append(
                    '-' * len(
                        dependency.get_label()
                    )
                )
                text_legal_list.append(
                    dependency.get_label().strip()
                )
                text_legal_list.append(
                    '-' * len(
                        dependency.get_label()
                    )
                )

                for line in text_legal.split('\n'):
                    line_length = 0
                    new_line = []

                    for word in line.strip().split():
                        if line_length + len(word) > 79:
                            text_legal_list.append(
                                ' '.join(new_line)
                            )
                            new_line = [word]
                            line_length = 0
                        else:
                            new_line.append(word)
                            line_length += len(word)

                    text_legal_list.append(
                        ' '.join(new_line)
                    )

                text_legal_list.append('\n')

        self.fields['text'].initial = '\n'.join(text_legal_list)
