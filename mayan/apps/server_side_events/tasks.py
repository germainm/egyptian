from django.apps import apps

from mayan.celery import app


@app.task(ignore_result=True)
def task_stream_event_stale_delete():
    StreamEvent = apps.get_model(
        app_label='server_side_events', model_name='StreamEvent'
    )
    StreamEvent.objects.stale_delete()
