from django.apps import apps

from mayan.celery import app

from .settings import (
    setting_deduplication_queued_interval,
    setting_deduplication_stale_interval
)


@app.task(ignore_result=True)
def task_deduplication_entry_stale_delete():
    TaskDeduplicationEntry = apps.get_model(
        app_label='task_manager', model_name='TaskDeduplicationEntry'
    )

    queued_interval = setting_deduplication_queued_interval.value
    stale_interval = setting_deduplication_stale_interval.value

    TaskDeduplicationEntry.objects.do_stale_delete(
        queued_interval=queued_interval, stale_interval=stale_interval
    )
