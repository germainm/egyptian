
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0002_taskdeduplicationentry_datetime_started'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskdeduplicationentry',
            name='is_dirty',
            field=models.BooleanField(default=False, help_text='A new request for the same unit of work arrived after the task began performing it, therefore too late for the task to take it into account. The work is dispatched once more when the task completes.', verbose_name='Is dirty?'),
        ),
    ]
