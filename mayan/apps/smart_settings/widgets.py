from django.template.loader import render_to_string


def setting_widget(instance):
    help_text = instance.help_text or ''
    context = {'help_text': help_text, 'setting': instance}

    return render_to_string(
        context=context,
        template_name='smart_settings/widgets/setting_name.html'
    )
