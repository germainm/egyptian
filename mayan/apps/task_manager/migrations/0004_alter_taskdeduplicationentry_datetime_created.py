
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0003_alter_taskdeduplicationentry_is_dirty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskdeduplicationentry',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, db_index=True, help_text='Date and time the work was requested or last re-dispatched. A marker whose work has not begun stops suppressing requests once this is older than the queued interval, which is what allows a worker that ended before publishing its task to recover without intervention.', verbose_name='Created'),
        ),
    ]
