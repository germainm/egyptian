from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='StoredDashboard',
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True, primary_key=True, serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'name', models.CharField(
                        max_length=128, unique=True, verbose_name='Name'
                    )
                )
            ],
            options={
                'verbose_name': 'Stored dashboard',
                'verbose_name_plural': 'Stored dashboards',
                'ordering': ('name',)
            }
        )
    ]
