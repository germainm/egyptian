from django.db import migrations, models

from mayan.apps.storage.hashing import chunk_hash_file_object


def code_asset_file_hash_update(apps, schema_editor):
    Asset = apps.get_model(app_label='converter', model_name='Asset')

    queryset = Asset.objects.using(
        alias=schema_editor.connection.alias
    ).all()

    for asset in queryset:
        try:
            with asset.file.storage.open(name=asset.file.name) as file_object:
                hash_object = chunk_hash_file_object(file_object=file_object)
        except Exception:
            continue
        else:
            asset.file_hash = hash_object.hexdigest()
            asset.save(
                update_fields=('file_hash',)
            )


class Migration(migrations.Migration):
    dependencies = [
        ('converter', '0020_auto_20230116_0640')
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='file_hash',
            field=models.CharField(
                blank=True, editable=False, help_text='A hash/checksum '
                'generated from the asset file. Used to invalidate cached '
                'images that use the asset when the asset file changes.',
                max_length=64, null=True, verbose_name='File hash'
            )
        ),
        migrations.RunPython(
            code=code_asset_file_hash_update,
            reverse_code=migrations.RunPython.noop
        )
    ]
