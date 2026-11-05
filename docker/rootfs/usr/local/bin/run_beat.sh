#!/bin/sh

echo "Executing \`run_beat\`."

MAYAN_BEAT_LOG_LEVEL="${MAYAN_BEAT_LOG_LEVEL:-${MAYAN_WORKER_LOG_LEVEL:-${MAYAN_LOGGING_LEVEL:-ERROR}}}"

MAYAN_BEAT_NICE_LEVEL="${MAYAN_BEAT_NICE_LEVEL:-1}"

exec nice -n "${MAYAN_BEAT_NICE_LEVEL}" \
    "${MAYAN_PYTHON_BIN_DIR}celery" \
    -A mayan \
    beat \
    --loglevel="${MAYAN_BEAT_LOG_LEVEL}" \
    --pidfile= \
    "${@}"
