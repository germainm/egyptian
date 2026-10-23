import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('appearance', '0004_remove_userthemesetting_theme_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL)
    ]

    operations = [
        migrations.CreateModel(
            name='UserSetting',
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True, primary_key=True, serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'namespace', models.CharField(
                        db_index=True, help_text='Axis or frontend that '
                        'owns this setting.', max_length=64,
                        verbose_name='Namespace'
                    )
                ),
                (
                    'key', models.CharField(
                        db_index=True, max_length=64, verbose_name='Key'
                    )
                ),
                (
                    'value', models.TextField(
                        blank=True, verbose_name='Value'
                    )
                ),
                (
                    'user', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='appearance_settings',
                        to=settings.AUTH_USER_MODEL, verbose_name='User'
                    )
                )
            ],
            options={
                'verbose_name': 'User setting',
                'verbose_name_plural': 'User settings',
                'ordering': ('namespace', 'key'),
                'unique_together': {
                    ('user', 'namespace', 'key')
                }
            }
        )
    ]
