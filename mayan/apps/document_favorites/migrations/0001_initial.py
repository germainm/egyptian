from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def code_content_type_rename_forward(apps, schema_editor):
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )

    ContentType.objects.filter(
        app_label='documents', model='favoritedocument'
    ).update(app_label='document_favorites')
    ContentType.objects.filter(
        app_label='documents', model='favoritedocumentproxy'
    ).update(app_label='document_favorites')


def code_content_type_rename_backward(apps, schema_editor):
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )

    ContentType.objects.filter(
        app_label='document_favorites', model='favoritedocument'
    ).update(app_label='documents')
    ContentType.objects.filter(
        app_label='document_favorites', model='favoritedocumentproxy'
    ).update(app_label='documents')


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('documents', '0092_alter_favoritedocument_unique_together'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL)
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='FavoriteDocument',
                    fields=[
                        (
                            'id', models.AutoField(
                                auto_created=True, primary_key=True,
                                serialize=False, verbose_name='ID'
                            )
                        ),
                        (
                            'datetime_added', models.DateTimeField(
                                auto_now=True, db_index=True,
                                verbose_name='Date and time added'
                            )
                        ),
                        (
                            'document', models.ForeignKey(
                                editable=False,
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='favorites',
                                to='documents.document',
                                verbose_name='Document'
                            )
                        ),
                        (
                            'user', models.ForeignKey(
                                editable=False,
                                on_delete=django.db.models.deletion.CASCADE,
                                to=settings.AUTH_USER_MODEL,
                                verbose_name='User'
                            )
                        )
                    ],
                    options={
                        'verbose_name': 'Favorite document',
                        'verbose_name_plural': 'Favorite documents',
                        'ordering': ('datetime_added',),
                        'db_table': 'documents_favoritedocument',
                        'unique_together': {('document', 'user')}
                    }
                ),
                migrations.CreateModel(
                    name='FavoriteDocumentProxy',
                    fields=[],
                    options={
                        'proxy': True,
                        'indexes': [],
                        'constraints': []
                    },
                    bases=('documents.document',)
                )
            ]
        ),
        migrations.RunPython(
            code=code_content_type_rename_forward,
            reverse_code=code_content_type_rename_backward
        )
    ]
