from django.db import migrations


def code_document_latest_file_populate(apps, schema_editor):
    cursor_main = schema_editor.connection.create_cursor(
        name='document_file_latest'
    )
    cursor_document_file_latest_update = schema_editor.connection.cursor()

    query_main = '''
        SELECT
            {documents_document}.{id}, {documents_documentfile_latest}.{id}
        FROM (
            SELECT
                {documents_documentfile_timestamp_max}.{document_id}, {documents_documentfile}.{id}
            FROM {documents_documentfile}, (
                SELECT
                    {document_id}, MAX({timestamp}) as {timestamp_max}
                FROM
                    {documents_documentfile}
                GROUP BY
                    {document_id}
            ) AS {documents_documentfile_timestamp_max}
            WHERE {documents_documentfile}.{timestamp} = {documents_documentfile_timestamp_max}.{timestamp_max}
            AND {documents_documentfile}.{document_id} = {documents_documentfile_timestamp_max}.{document_id}
        ) as {documents_documentfile_latest}
        INNER JOIN
          {documents_document}
        ON
          {documents_document}.{id} = {documents_documentfile_latest}.{document_id}
    '''.format(
        documents_document=schema_editor.connection.ops.quote_name(
            name='documents_document'
        ),
        documents_documentfile=schema_editor.connection.ops.quote_name(
            name='documents_documentfile'
        ),
        documents_documentfile_latest=schema_editor.connection.ops.quote_name(
            name='documents_documentfile_latest'
        ),
        documents_documentfile_timestamp_max=schema_editor.connection.ops.quote_name(
            name='documents_documentfile_timestamp_max'
        ),
        document_id=schema_editor.connection.ops.quote_name(
            name='document_id'
        ),
        id=schema_editor.connection.ops.quote_name(name='id'),
        timestamp=schema_editor.connection.ops.quote_name(name='timestamp'),
        timestamp_max=schema_editor.connection.ops.quote_name(
            name='timestamp_max'
        )
    )

    cursor_main.execute(query_main)

    FETCH_SIZE = 100000

    quoted_documents_document = schema_editor.connection.ops.quote_name(
        name='documents_document'
    )
    quoted_file_latest_id = schema_editor.connection.ops.quote_name(
        name='file_latest_id'
    )
    quoted_id = schema_editor.connection.ops.quote_name(name='id')

    while True:
        rows = cursor_main.fetchmany(FETCH_SIZE)
        for row in rows:
            query = f'''
                UPDATE {quoted_documents_document}
                    SET {quoted_file_latest_id} = {row[1]}
                WHERE {quoted_id} = {row[0]};
            '''

            cursor_document_file_latest_update.execute(query)

        if not rows:
            break


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0085_document_file_latest')
    ]

    operations = [
        migrations.RunPython(
            code=code_document_latest_file_populate,
            reverse_code=migrations.RunPython.noop
        )
    ]
