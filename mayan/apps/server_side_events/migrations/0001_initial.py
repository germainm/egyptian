import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL)
    ]

    operations = [
        migrations.CreateModel(
            name='StreamEvent',
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True, primary_key=True, serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'event_type', models.CharField(
                        db_index=True, max_length=128,
                        verbose_name='Event type'
                    )
                ),
                (
                    'payload', models.TextField(
                        blank=True, verbose_name='Payload'
                    )
                ),
                (
                    'datetime_created', models.DateTimeField(
                        auto_now_add=True, db_index=True,
                        verbose_name='Date and time created'
                    )
                ),
                (
                    'user', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='server_side_events',
                        to=settings.AUTH_USER_MODEL, verbose_name='User'
                    )
                ),
            ],
            options={
                'verbose_name': 'Stream event',
                'verbose_name_plural': 'Stream events',
                'ordering': ('id',)
            }
        )
    ]
