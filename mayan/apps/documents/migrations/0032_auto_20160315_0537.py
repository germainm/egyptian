from django.db import connection, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0031_convert_uuid')
    ]

    operations = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if connection.vendor == 'postgresql':
            self.operations = [
                migrations.RunSQL(
                    sql='ALTER TABLE documents_document ALTER COLUMN uuid SET DATA TYPE UUID USING uuid::uuid;',
                    reverse_sql=migrations.RunSQL.noop
                )
            ]
