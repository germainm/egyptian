#!/bin/sh
set -e

echo "Executing \`run_frontend\`."

set -- \
    --bind "${MAYAN_GUNICORN_BIND_ADDRESS:-0.0.0.0:8000}" \
    --chdir "${MAYAN_INSTALL_DIR}" \
    --env DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
    --no-control-socket \
    --limit-request-line "${MAYAN_GUNICORN_LIMIT_REQUEST_LINE}" \
    --log-level "${MAYAN_GUNICORN_LOG_LEVEL:-error}" \
    --max-requests "${MAYAN_GUNICORN_MAX_REQUESTS}" \
    --max-requests-jitter "${MAYAN_GUNICORN_REQUESTS_JITTER}" \
    --timeout "${MAYAN_GUNICORN_TIMEOUT}" \
    --worker-class "${MAYAN_GUNICORN_WORKER_CLASS}" \
    --workers "${MAYAN_GUNICORN_WORKERS}"

if [ -n "${MAYAN_GUNICORN_TEMPORARY_DIRECTORY}" ]; then
    set -- "${@}" "${MAYAN_GUNICORN_TEMPORARY_DIRECTORY}"
fi

set -- "${@}" mayan.wsgi

exec "${MAYAN_PYTHON_BIN_DIR}gunicorn" "${@}"
