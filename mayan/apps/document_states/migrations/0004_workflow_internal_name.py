from django.db import migrations, models
from django.utils.text import slugify

from mayan.apps.common.validators import validate_internal_name


def code_generate_internal_name(apps, schema_editor):
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )
    field_length = Workflow._meta.get_field(
        field_name='internal_name'
    ).max_length
    internal_names = set()

    alias = schema_editor.connection.alias

    queryset = Workflow.objects.using(alias=alias).order_by('pk')

    for workflow in queryset:
        internal_name = slugify(workflow.label).replace('-', '_')

        candidate = internal_name[:field_length]
        index = 0
        while candidate in internal_names:
            index = index + 1
            suffix = '_{}'.format(index)
            candidate = '{}{}'.format(
                internal_name[:field_length - len(suffix)], suffix
            )

        workflow.internal_name = candidate
        internal_names.add(candidate)
        workflow.save(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('document_states', '0003_auto_20170325_0447')
    ]

    operations = [
        migrations.AddField(
            model_name='workflow',
            name='internal_name',
            field=models.CharField(
                db_index=False, default=' ',
                help_text='This value will be used by other apps to '
                'reference this workflow. Can only contain letters, '
                'numbers, and underscores.', max_length=255, unique=False,
                validators=[
                    validate_internal_name
                ], verbose_name='Internal name'
            )
        ),
        migrations.RunPython(
            code=code_generate_internal_name,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name='workflow',
            name='internal_name',
            field=models.CharField(
                db_index=True,
                help_text='This value will be used by other apps to '
                'reference this workflow. Can only contain letters, '
                'numbers, and underscores.', max_length=255, unique=True,
                validators=[
                    validate_internal_name
                ], verbose_name='Internal name'
            )
        )
    ]
