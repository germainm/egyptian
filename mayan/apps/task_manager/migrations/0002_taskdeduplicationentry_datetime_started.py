
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskdeduplicationentry',
            name='datetime_started',
            field=models.DateTimeField(blank=True, db_index=True, help_text='Date and time a worker began performing the work. Until it is set, the task the marker stands for is still waiting in the queue and has not read the object it will act on, so a request arriving in that period asks for work the queued task is already going to perform.', null=True, verbose_name='Started'),
        ),
    ]
