import pycountry

from django.db import migrations


def code_change_bibliographic_to_terminology(apps, schema_editor):
    Document = apps.get_model(app_label='documents', model_name='Document')

    alias = schema_editor.connection.alias

    queryset = Document.objects.using(alias=alias).all()

    for document in queryset:
        try:
            language = pycountry.languages.get(
                bibliographic=document.language
            )
        except (KeyError, TypeError):
            language = None

        if language is None:
            document.language = 'eng'
        else:
            document.language = getattr(
                language, 'terminology', None
            ) or language.alpha_3

        document.save(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0024_auto_20150715_0714')
    ]

    operations = [
        migrations.RunPython(
            code=code_change_bibliographic_to_terminology,
            reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]
