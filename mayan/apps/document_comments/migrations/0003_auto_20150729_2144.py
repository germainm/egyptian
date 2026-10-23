from django.conf import settings
from django.db import migrations


def code_migrate_old_comments(apps, schema_editor):

    try:
        from django.contrib.comments.models import Comment as OldComment
    except ImportError:
        pass
    else:

        Comment = apps.get_model(
            app_label='document_comments', model_name='Comment'
        )
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        User = apps.get_model(
            *settings.AUTH_USER_MODEL.split('.')
        )

        for old_comment in OldComment.objects.using(alias=schema_editor.connection.alias).all():
            comment = Comment(
                document=Document.objects.using(
                    alias=schema_editor.connection.alias
                ).get(pk=old_comment.object_pk),
                user=User(old_comment.user.pk),
                comment=old_comment.comment,
                submit_date=old_comment.submit_date,
            )
            comment.save()


class Migration(migrations.Migration):
    dependencies = [
        ('document_comments', '0002_auto_20150729_2144'),
        ('documents', '0001_initial'),
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL)
    ]

    operations = [
        migrations.RunPython(
            code=code_migrate_old_comments,
            reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]
