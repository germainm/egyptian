
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaskDeduplicationEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dotted_path', models.CharField(db_index=True, help_text='Python path of the task type the marker suppresses.', max_length=255, verbose_name='Dotted path')),
                ('key', models.TextField(help_text='Serialized keyword arguments identifying the unit of work requested.', verbose_name='Key')),
                ('key_hash', models.CharField(help_text='Hash of the key. The unique constraint is applied to this field and not to the key itself because the length of a key is decided by the task requesting the work, and an index over an unbounded column exceeds the size limit of some database managers.', max_length=64, verbose_name='Key hash')),
                ('datetime_created', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Date and time the work was requested or last re-dispatched. A marker older than the stale interval stops suppressing work, which is what allows a worker that ended before releasing its marker to recover without intervention.', verbose_name='Created')),
                ('is_dirty', models.BooleanField(default=False, help_text='A new request for the same unit of work arrived while the task was queued or executing. The work is dispatched once more when the task completes.', verbose_name='Is dirty?')),
            ],
            options={
                'verbose_name': 'Task deduplication entry',
                'verbose_name_plural': 'Task deduplication entries',
                'ordering': ('datetime_created',),
                'constraints': [models.UniqueConstraint(fields=('dotted_path', 'key_hash'), name='task_manager_taskdeduplicationentry_unique_key')],
            },
        ),
    ]
