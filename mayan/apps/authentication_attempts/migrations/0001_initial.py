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
            name='LoginAttempt',
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True, primary_key=True, serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'username', models.CharField(
                        db_index=True,
                        help_text='The username exactly as it was supplied '
                        'for the authentication attempt. For failed attempts '
                        'this may not match any existing account.',
                        max_length=254, verbose_name='Username'
                    )
                ),
                (
                    'result', models.CharField(
                        choices=[
                            ('failure', 'Failure'), ('success', 'Success')
                        ], db_index=True,
                        help_text='Whether the authentication attempt '
                        'succeeded or failed.', max_length=32,
                        verbose_name='Result'
                    )
                ),
                (
                    'source', models.CharField(
                        choices=[
                            ('api', 'API'), ('session', 'Session')
                        ], default='session',
                        help_text='The subsystem through which the '
                        'authentication was attempted, such as the '
                        'interactive session or the API.',
                        max_length=32, verbose_name='Source'
                    )
                ),
                (
                    'ip_address', models.GenericIPAddressField(
                        blank=True,
                        help_text='The client address as resolved by the '
                        'lockout layer. Behind a reverse proxy this is '
                        'only meaningful when the proxy trust is '
                        'configured; treat it as best effort.',
                        null=True, verbose_name='IP address'
                    )
                ),
                (
                    'user_agent', models.TextField(
                        blank=True,
                        help_text='Information about the web browser '
                        'or application used to make the login '
                        'attempt.', verbose_name='User agent'
                    )
                ),
                (
                    'datetime', models.DateTimeField(
                        auto_now_add=True, db_index=True,
                        verbose_name='Date and time'
                    )
                ),
                (
                    'user', models.ForeignKey(
                        blank=True,
                        help_text='The existing account that the supplied '
                        'username resolved to, if any.', null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='login_attempts',
                        to=settings.AUTH_USER_MODEL, verbose_name='User'
                    )
                )
            ],
            options={
                'verbose_name': 'Login attempt',
                'verbose_name_plural': 'Login attempts',
                'ordering': ('-datetime',)
            }
        )
    ]
