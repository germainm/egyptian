#!/bin/sh
set -e

echo "Executing \`run_frontend\`."

# Build argv safely and only add the tmp-dir arg if non-empty.
set -- \
    --bind 0.0.0.0:8000 \
    --chdir "${MAYAN_INSTALL_DIR}" \
    --env DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
    --limit-request-line "${MAYAN_GUNICORN_LIMIT_REQUEST_LINE}" \
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
