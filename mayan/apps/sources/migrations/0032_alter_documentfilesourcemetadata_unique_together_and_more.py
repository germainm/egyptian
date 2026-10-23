from django.core.exceptions import FieldDoesNotExist
from django.db import migrations, models
from django.db.utils import DatabaseError


def code_do_unique_on_columns_drop(apps, schema_editor):
    Model = apps.get_model(
        app_label='sources', model_name='DocumentFileSourceMetadata'
    )

    connection = schema_editor.connection
    database_columns = ('document_file_id', 'key')
    field_names = ('document_file', 'key')
    table_name = Model._meta.db_table
    target = set(database_columns)

    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(
            cursor=cursor, table_name=table_name
        )

        for constraint_name, constraint_data in constraints.items():
            constraint_columns = set(
                constraint_data.get('columns') or []
            )

            if constraint_data.get('unique') and constraint_columns == target:
                try:
                    schema_editor.remove_constraint(
                        model=Model,
                        constraint=models.UniqueConstraint(
                            fields=field_names, name=constraint_name
                        )
                    )
                except DatabaseError:
                    try:
                        schema_editor.remove_index(
                            model=Model,
                            index=models.Index(
                                fields=field_names, name=constraint_name
                            )
                        )
                    except DatabaseError:
                        """It's neither or deleted already."""
                else:
                    continue


def do_source_column_remove_if_exists(apps, schema_editor):
    Model = apps.get_model(
        app_label='sources', model_name='DocumentFileSourceMetadata'
    )

    connection = schema_editor.connection
    source_field_name = 'source'
    source_column_name = 'source_id'
    table = Model._meta.db_table

    with connection.cursor() as cursor:
        table_field_list = connection.introspection.get_table_description(
            cursor=cursor, table_name=table
        )

        columns_set = {
            field.name for field in table_field_list
        }

        if source_column_name not in columns_set:
            return
        else:
            try:
                field = Model._meta.get_field(field_name=source_field_name)
            except FieldDoesNotExist:
                field = models.IntegerField(null=True)
                field.set_attributes_from_name(name=source_field_name)
                field.db_column = source_column_name

            schema_editor.remove_field(model=Model, field=field)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0090_alter_documentversion_active'),
        ('sources', '0031_alter_documentfilesourcemetadata_value')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=code_do_unique_on_columns_drop,
                    reverse_code=migrations.RunPython.noop
                )
            ],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="documentfilesourcemetadata",
                    unique_together=set()
                )
            ]
        ),
        migrations.AlterUniqueTogether(
            name='documentfilesourcemetadata', unique_together={
                ('document_file', 'key')
            }
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=do_source_column_remove_if_exists,
                    reverse_code=migrations.RunPython.noop
                )
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='documentfilesourcemetadata',
                    name='source'
                )
            ]
        )
    ]
