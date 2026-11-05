#!/bin/sh

echo "Executing \`run_worker\`."

MAYAN_WORKER_LOG_LEVEL="${MAYAN_WORKER_LOG_LEVEL:-${MAYAN_LOGGING_LEVEL:-ERROR}}"

case "${1:-}" in
    ''|-*)
        MAYAN_WORKER_NAME_GIVEN=false
        ;;
    *)
        MAYAN_WORKER_NAME_GIVEN=true
        ;;
esac

if [ "${MAYAN_WORKER_NAME_GIVEN}" = true ]; then
    MAYAN_WORKER_NAME="${MAYAN_WORKER_NAME:-$1}"
    shift
fi

export MAYAN_WORKER_NAME

if [ "${MAYAN_WORKER_NAME}" ]; then
    MAYAN_WORKER_NAME_UPPER=$(echo "${MAYAN_WORKER_NAME}" | tr '[:lower:]' '[:upper:]')
else
    MAYAN_WORKER_NAME_UPPER=
fi

if [ "${MAYAN_WORKER_NAME_UPPER}" ]; then
    MAYAN_WORKER_NICE_LEVEL_DEFAULT=$(printenv "MAYAN_${MAYAN_WORKER_NAME_UPPER}_NICE_LEVEL" || true)
else
    MAYAN_WORKER_NICE_LEVEL_DEFAULT=
fi

MAYAN_WORKER_NICE_LEVEL="${MAYAN_WORKER_NICE_LEVEL:-${MAYAN_WORKER_NICE_LEVEL_DEFAULT:-0}}"

if [ ! "${MAYAN_QUEUE_LIST}" ]; then
    if [ ! "${MAYAN_WORKER_NAME}" ]; then
        echo "Must specify either \`MAYAN_QUEUE_LIST\` or \`MAYAN_WORKER_NAME\`."
        exit 1
    else
        MAYAN_QUEUE_LIST=$("${MAYAN_PYTHON_BIN_DIR}mayan-edms.py" platforms_template worker_queues)
        MAYAN_QUEUE_LIST_EXIT_CODE=$?

        if [ ! "${MAYAN_QUEUE_LIST}" ]; then
            echo "Unable to resolve the queue list of the worker named \`${MAYAN_WORKER_NAME}\`."
            echo "\`platforms_template worker_queues\` exited with ${MAYAN_QUEUE_LIST_EXIT_CODE} and returned nothing."
            echo "This is expected when the worker starts before the database is ready or before the setup has finished, and the worker is restarted until it is."
            echo "If it persists, the name given does not match any worker; \`mayan-edms.py platforms_template worker_queues\` lists the queues of \`MAYAN_WORKER_NAME\`."
            exit 1
        fi
    fi
fi

argument_list_has_option() {
    option_long="$1"
    option_short="$2"
    shift 2

    for argument in "${@}"; do
        case "${argument}" in
            "${option_long}"|"${option_long}"=*)
                return 0
                ;;
        esac

        if [ "${option_short}" ]; then
            if [ "${argument}" = "${option_short}" ]; then
                return 0
            fi
        fi
    done

    return 1
}

MAYAN_WORKER_ARGUMENT_LIST=""

for MAYAN_WORKER_LIMIT_NAME in CONCURRENCY MAX_MEMORY_PER_CHILD MAX_TASKS_PER_CHILD; do
    case "${MAYAN_WORKER_LIMIT_NAME}" in
        CONCURRENCY)
            MAYAN_WORKER_LIMIT_OPTION=--concurrency
            MAYAN_WORKER_LIMIT_OPTION_SHORT=-c
            ;;
        MAX_MEMORY_PER_CHILD)
            MAYAN_WORKER_LIMIT_OPTION=--max-memory-per-child
            MAYAN_WORKER_LIMIT_OPTION_SHORT=
            ;;
        MAX_TASKS_PER_CHILD)
            MAYAN_WORKER_LIMIT_OPTION=--max-tasks-per-child
            MAYAN_WORKER_LIMIT_OPTION_SHORT=
            ;;
    esac

    if argument_list_has_option "${MAYAN_WORKER_LIMIT_OPTION}" "${MAYAN_WORKER_LIMIT_OPTION_SHORT}" "${@}"; then
        continue
    fi

    MAYAN_WORKER_LIMIT_VALUE=
    MAYAN_WORKER_LIMIT_IS_SET=false

    if [ "${MAYAN_WORKER_NAME_UPPER}" ]; then
        if MAYAN_WORKER_LIMIT_VALUE=$(printenv "MAYAN_${MAYAN_WORKER_NAME_UPPER}_${MAYAN_WORKER_LIMIT_NAME}"); then
            MAYAN_WORKER_LIMIT_IS_SET=true
        fi
    fi

    if [ "${MAYAN_WORKER_LIMIT_IS_SET}" = false ]; then
        MAYAN_WORKER_LIMIT_NUMBER=$(printenv "MAYAN_WORKER_${MAYAN_WORKER_LIMIT_NAME}" || true)

        if [ "${MAYAN_WORKER_LIMIT_NUMBER}" ] && [ "${MAYAN_WORKER_LIMIT_NUMBER}" != 0 ]; then
            MAYAN_WORKER_LIMIT_VALUE="${MAYAN_WORKER_LIMIT_OPTION}=${MAYAN_WORKER_LIMIT_NUMBER}"
        fi
    fi

    if [ "${MAYAN_WORKER_LIMIT_VALUE}" ]; then
        MAYAN_WORKER_ARGUMENT_LIST="${MAYAN_WORKER_ARGUMENT_LIST} ${MAYAN_WORKER_LIMIT_VALUE}"
    fi
done

exec nice -n "${MAYAN_WORKER_NICE_LEVEL}" \
    "${MAYAN_PYTHON_BIN_DIR}celery" \
    -A mayan \
    worker \
    --loglevel="${MAYAN_WORKER_LOG_LEVEL}" \
    -Ofair \
    --queues="${MAYAN_QUEUE_LIST}" \
    ${MAYAN_WORKER_ARGUMENT_LIST} \
    "${@}"
