from django.db import migrations

from mayan.apps.events.classes import ModelEventType


def code_populate_index_template_event_triggers(apps, schema_editor):
    IndexTemplate = apps.get_model(
        app_label='document_indexing', model_name='IndexTemplate'
    )
    IndexTemplateEventTrigger = apps.get_model(
        app_label='document_indexing', model_name='IndexTemplateEventTrigger'
    )

    document_event_type_list = []
    for model, event_type_list in ModelEventType._registry.items():
        if model._meta.app_label == 'documents' and model._meta.model_name == 'document':
            document_event_type_list.extend(event_type_list)

    for index_template in IndexTemplate.objects.all():
        entries = [
            IndexTemplateEventTrigger(
                index_template=index_template,
                stored_event_type_id=event_type.get_stored_event_type().pk
            ) for event_type in document_event_type_list
        ]

        IndexTemplateEventTrigger.objects.bulk_create(
            objs=entries, ignore_conflicts=True
        )


def code_populate_index_template_event_triggers_reverse(apps, schema_editor):
    IndexTemplateEventTrigger = apps.get_model(
        app_label='document_indexing', model_name='IndexTemplateEventTrigger'
    )
    IndexTemplateEventTrigger.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('document_indexing', '0027_indextemplateeventtrigger')
    ]

    operations = [
        migrations.RunPython(
            code=code_populate_index_template_event_triggers,
            reverse_code=code_populate_index_template_event_triggers_reverse
        )
    ]
