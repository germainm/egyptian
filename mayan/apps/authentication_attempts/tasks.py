from mayan.celery import app

from .login_retention_backends import LoginAttemptRetentionBackend
from .settings import (
    setting_login_attempt_retention_backend,
    setting_login_attempt_retention_backend_arguments
)


@app.task(ignore_result=True)
def task_login_attempt_retention():
    backend_path = setting_login_attempt_retention_backend.value

    if backend_path:
        backend_class = LoginAttemptRetentionBackend.get(name=backend_path)
        backend_instance = backend_class(
            **setting_login_attempt_retention_backend_arguments.value
        )
        backend_instance.execute()
