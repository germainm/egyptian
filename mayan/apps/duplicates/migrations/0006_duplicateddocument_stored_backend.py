from django.db import migrations, models
import django.db.models.deletion


class AddFieldDynamicDefault(migrations.AddField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        StoredDuplicateBackend = from_state.apps.get_model(
            app_label='duplicates', model_name='StoredDuplicateBackend'
        )

        stored_backend = StoredDuplicateBackend.objects.using(
            alias=schema_editor.connection.alias
        ).first()

        if stored_backend:
            stored_backend_id = stored_backend.pk

            self.field.default = stored_backend_id

        super().database_forwards(
            app_label=app_label, schema_editor=schema_editor,
            from_state=from_state, to_state=to_state
        )


class Migration(migrations.Migration):
    dependencies = [
        ('duplicates', '0005_auto_20201130_0747')
    ]

    operations = [
        AddFieldDynamicDefault(
            model_name='duplicateddocument',
            name='stored_backend',
            field=models.ForeignKey(
                default=None, on_delete=django.db.models.deletion.CASCADE,
                related_name='duplicate_entries',
                to='duplicates.StoredDuplicateBackend',
                verbose_name='Stored duplicate backend'
            ),
            preserve_default=False
        )
    ]
