#!/bin/sh

# -e  Exit immediately if a command exits with a non-zero status.
set -e

any_to_bool () {
    local argument="$(echo ${1} | tr '[:upper:]' '[:lower:]')"

    if [ "${argument}" = true ] || [ "${argument}" = t ] || [ "${argument}" = yes ] || [ "${argument}" = y ] || [ "${argument}" = 1 ]; then
        local function_result=True
        echo "$function_result"
    fi
}

apt_get_install() {
    apt-get update
    apt-get install --auto-remove --force-yes --no-install-recommends --yes "${@}"
    apt-get clean
    rm --force --recursive /var/lib/apt/lists/*
}

banner_show() {
    cat <<'EOF'


        /\
       /  \      Egyptian 4.12.2
      /    \     Based on Mayan EDMS®
     /______\

 Mayan EDMS: Copyright 2026 Roberto Rosario
 Egyptian modifications: Copyright 2026 mypalace.ca
 "Mayan EDMS" is a registered trademark of Roberto Rosario.

 License: GPL 2.0

 Website: https://egyptian-apps.mypalace.ca


EOF
}

build_font_cache() {
    # Clear the fontconfig cache.
    echo "Building font information cache files."
    /usr/bin/fc-cache
}

initial_setup() {
    echo "Executing \`initial_setup\`."

    runuser --user mayan -- "${MAYAN_BIN}" common_initial_setup --force --no-dependencies
}

initial_setup_or_perform_upgrade() {
    # Check if this is a new install, otherwise try to upgrade the existing
    # installation on subsequent starts.
    if [ ! -f "${INSTALL_FLAG}" ]; then
        initial_setup
    else
        perform_upgrade
    fi
}

os_package_installs() {
    echo "Executing \`os_package_installs\`."
    if [ "${MAYAN_APT_INSTALLS}" ]; then
        DEBIAN_FRONTEND=noninteractive apt_get_install ${MAYAN_APT_INSTALLS}
    else
        echo "Nothing to install."
    fi
}

perform_upgrade() {
    echo "Executing \`perform_upgrade\`."
    runuser --user mayan -- "${MAYAN_BIN}" common_perform_upgrade --no-dependencies
}

pip_installs() {
    echo "Executing \`pip_installs\`."
    if [ "${MAYAN_PIP_INSTALLS}" ]; then
        runuser --user mayan -- "${MAYAN_PIP_BIN}" install ${MAYAN_PIP_INSTALLS}
    else
        echo "Nothing to install."
    fi
}

update_uid_gid() {
    echo "Executing \`update_uid_gid\`."

    result="$(any_to_bool ${MAYAN_COMMON_DISABLE_LOCAL_STORAGE})"

    if [ "${result}" ]; then
        echo "Skipping uid and gid update."
    else
        # Change the owner of the /var/lib/mayan always to allow adding the
        # initial files. Top level only.
        chown mayan:mayan "${MAYAN_MEDIA_ROOT}"

        echo "Modifying gid and uid definitions of the user."
        groupmod mayan --gid "${MAYAN_USER_GID}" --non-unique
        usermod mayan --uid "${MAYAN_USER_UID}" --non-unique

        if [ "${MAYAN_USER_UID}" -ne 1000 ] || [ "${MAYAN_USER_GID}" -ne 1000 ]; then
            echo "Updating file ownership. This might take a while if there are many documents."
            chown --recursive mayan:mayan "${MAYAN_INSTALL_DIR}" "${MAYAN_STATIC_ROOT}"
            if [ "${MAYAN_SKIP_CHOWN_ON_STARTUP}" = "true" ]; then
                echo "Skipping \`chown\` command on startup as instructed."
            else
                chown --recursive mayan:mayan "${MAYAN_MEDIA_ROOT}"
            fi
        fi
    fi
}

# Start execution here.
banner_show
echo "Starting \`entrypoint.sh\`."
INSTALL_FLAG=/var/lib/mayan/system/SECRET_KEY
CELERY_CONCURRENCY_ARGUMENT=--concurrency=
CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT=--max-memory-per-child=
CELERY_MAX_TASKS_PER_CHILD_ARGUMENT=--max-tasks-per-child=

export MAYAN_USER_GID="${MAYAN_USER_GID:-1000}"
export MAYAN_USER_UID="${MAYAN_USER_UID:-1000}"

export MAYAN_ALLOWED_HOSTS='["*"]'
export MAYAN_BIN=/opt/mayan-edms/bin/mayan-edms.py
export MAYAN_INSTALL_DIR=/opt/mayan-edms
export MAYAN_PYTHON_BIN_DIR=/opt/mayan-edms/bin/
export MAYAN_MEDIA_ROOT=/var/lib/mayan
export MAYAN_SETTINGS_MODULE="${MAYAN_SETTINGS_MODULE:-mayan.settings.production}"

# Set DJANGO_SETTINGS_MODULE to MAYAN_SETTINGS_MODULE to avoid two
# different environment variables for the same setting.
export DJANGO_SETTINGS_MODULE="${MAYAN_SETTINGS_MODULE}"

# Gunicorn

export MAYAN_GUNICORN_BIN="${MAYAN_PYTHON_BIN_DIR}gunicorn"
# Variables of the Supervisor configuration of Mayan EDMS 4.12.2 (defined in the
# [supervisord] section outside Docker).
export MAYAN_GUNICORN_BIND_ADDRESS="${MAYAN_GUNICORN_BIND_ADDRESS:-0.0.0.0:8000}"
export MAYAN_GUNICORN_LOG_LEVEL="${MAYAN_GUNICORN_LOG_LEVEL:-error}"
export MAYAN_BEAT_LOG_LEVEL="${MAYAN_BEAT_LOG_LEVEL:-ERROR}"
export MAYAN_BEAT_NICE_LEVEL="${MAYAN_BEAT_NICE_LEVEL:-1}"
export MAYAN_WORKER_LOG_LEVEL="${MAYAN_WORKER_LOG_LEVEL:-ERROR}"
export MAYAN_GUNICORN_REQUESTS_JITTER="${MAYAN_GUNICORN_REQUESTS_JITTER:-50}"
export MAYAN_GUNICORN_LIMIT_REQUEST_LINE="${MAYAN_GUNICORN_LIMIT_REQUEST_LINE:-4094}"
export MAYAN_GUNICORN_MAX_REQUESTS="${MAYAN_GUNICORN_MAX_REQUESTS:-500}"
export MAYAN_GUNICORN_WORKER_CLASS="${MAYAN_GUNICORN_WORKER_CLASS:-gevent}"
export MAYAN_GUNICORN_WORKERS="${MAYAN_GUNICORN_WORKERS:-3}"
export MAYAN_GUNICORN_TIMEOUT="${MAYAN_GUNICORN_TIMEOUT:-120}"

if mount | grep --quiet '/dev/shm'; then
    export MAYAN_GUNICORN_TEMPORARY_DIRECTORY="--worker-tmp-dir=/dev/shm"
else
    export MAYAN_GUNICORN_TEMPORARY_DIRECTORY=
fi

# Others

export MAYAN_PIP_BIN="${MAYAN_PYTHON_BIN_DIR}pip"
export MAYAN_STATIC_ROOT="${MAYAN_INSTALL_DIR}/static"
export MAYAN_SUPERVISOR_AUTORESTART="${MAYAN_SUPERVISOR_AUTORESTART:-false}"

# Setup worker environment variables. Used by the all-in-one profile only.

MAYAN_WORKER_A_CONCURRENCY="${MAYAN_WORKER_A_CONCURRENCY:-4}"

if [ "${MAYAN_WORKER_A_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_A_CONCURRENCY=
else
    MAYAN_WORKER_A_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_A_CONCURRENCY}"
fi
export MAYAN_WORKER_A_CONCURRENCY

MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD:-500000}"

if [ "${MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_A_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_A_MAX_TASKS_PER_CHILD:-4000}"

if [ "${MAYAN_WORKER_A_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_A_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_A_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_A_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_A_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_A_NICE_LEVEL="${MAYAN_WORKER_A_NICE_LEVEL:-0}"

MAYAN_WORKER_B_CONCURRENCY="${MAYAN_WORKER_B_CONCURRENCY:-8}"

if [ "${MAYAN_WORKER_B_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_B_CONCURRENCY=
else
    MAYAN_WORKER_B_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_B_CONCURRENCY}"
fi
export MAYAN_WORKER_B_CONCURRENCY

MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD:-1200000}"

if [ "${MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_B_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_B_MAX_TASKS_PER_CHILD:-10000}"

if [ "${MAYAN_WORKER_B_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_B_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_B_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_B_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_B_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_B_NICE_LEVEL="${MAYAN_WORKER_B_NICE_LEVEL:-2}"

MAYAN_WORKER_C_CONCURRENCY="${MAYAN_WORKER_C_CONCURRENCY:-4}"

if [ "${MAYAN_WORKER_C_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_C_CONCURRENCY=
else
    MAYAN_WORKER_C_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_C_CONCURRENCY}"
fi
export MAYAN_WORKER_C_CONCURRENCY

MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD:-1000000}"

if [ "${MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_C_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_C_MAX_TASKS_PER_CHILD:-4000}"

if [ "${MAYAN_WORKER_C_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_C_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_C_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_C_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_C_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_C_NICE_LEVEL="${MAYAN_WORKER_C_NICE_LEVEL:-10}"

MAYAN_WORKER_D_CONCURRENCY="${MAYAN_WORKER_D_CONCURRENCY:-2}"

if [ "${MAYAN_WORKER_D_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_D_CONCURRENCY=
else
    MAYAN_WORKER_D_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_D_CONCURRENCY}"
fi
export MAYAN_WORKER_D_CONCURRENCY

MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD:-1500000}"

if [ "${MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_D_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_D_MAX_TASKS_PER_CHILD:-2000}"

if [ "${MAYAN_WORKER_D_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_D_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_D_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_D_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_D_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_D_NICE_LEVEL="${MAYAN_WORKER_D_NICE_LEVEL:-15}"

MAYAN_WORKER_E_CONCURRENCY="${MAYAN_WORKER_E_CONCURRENCY:-4}"

if [ "${MAYAN_WORKER_E_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_E_CONCURRENCY=
else
    MAYAN_WORKER_E_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_E_CONCURRENCY}"
fi
export MAYAN_WORKER_E_CONCURRENCY

MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD:-500000}"

if [ "${MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_E_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_E_MAX_TASKS_PER_CHILD:-20000}"

if [ "${MAYAN_WORKER_E_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_E_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_E_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_E_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_E_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_E_NICE_LEVEL="${MAYAN_WORKER_E_NICE_LEVEL:-2}"

MAYAN_WORKER_F_CONCURRENCY="${MAYAN_WORKER_F_CONCURRENCY:-1}"

if [ "${MAYAN_WORKER_F_CONCURRENCY}" -eq 0 ]; then
    MAYAN_WORKER_F_CONCURRENCY=
else
    MAYAN_WORKER_F_CONCURRENCY="${CELERY_CONCURRENCY_ARGUMENT}${MAYAN_WORKER_F_CONCURRENCY}"
fi
export MAYAN_WORKER_F_CONCURRENCY

MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD="${MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD:-1000000}"

if [ "${MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD=
else
    MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD="${CELERY_MAX_MEMORY_PER_CHILD_ARGUMENT}${MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD}"
fi
export MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD

MAYAN_WORKER_F_MAX_TASKS_PER_CHILD="${MAYAN_WORKER_F_MAX_TASKS_PER_CHILD:-2000}"

if [ "${MAYAN_WORKER_F_MAX_TASKS_PER_CHILD}" -eq 0 ]; then
    MAYAN_WORKER_F_MAX_TASKS_PER_CHILD=
else
    MAYAN_WORKER_F_MAX_TASKS_PER_CHILD="${CELERY_MAX_TASKS_PER_CHILD_ARGUMENT}${MAYAN_WORKER_F_MAX_TASKS_PER_CHILD}"
fi
export MAYAN_WORKER_F_MAX_TASKS_PER_CHILD
export MAYAN_WORKER_F_NICE_LEVEL="${MAYAN_WORKER_F_NICE_LEVEL:-15}"


# Allow importing of user setting modules.
export PYTHONPATH="${PYTHONPATH}:${MAYAN_MEDIA_ROOT}"

echo "Executing pre setup script."
if [ "${MAYAN_DOCKER_SCRIPT_PRE_SETUP}" ]; then
    eval "${MAYAN_DOCKER_SCRIPT_PRE_SETUP}"
fi

"${MAYAN_PYTHON_BIN_DIR}python3" /usr/local/bin/wait.py ${MAYAN_DOCKER_WAIT}
update_uid_gid
os_package_installs || true
pip_installs || true
build_font_cache

echo "Executing post setup script."
if [ "${MAYAN_DOCKER_SCRIPT_POST_SETUP}" ]; then
    eval "${MAYAN_DOCKER_SCRIPT_POST_SETUP}"
fi

echo "Exiting \`entrypoint.sh\`."
echo "Executing final target: ${@}"
echo ""

case "$1" in

run_all)
    initial_setup_or_perform_upgrade
    /usr/local/bin/run_all.sh
    ;;

run_celery)
    shift
    exec runuser --user mayan -- /usr/local/bin/run_celery.sh "${@}"
    ;;

run_command)
    shift
    exec runuser --user mayan -- "${MAYAN_BIN}" "${@}"
    ;;

run_frontend)
    exec runuser --user mayan -- /usr/local/bin/run_frontend.sh
    ;;

run_initial_setup)
    initial_setup
    ;;

run_perform_upgrade)
    perform_upgrade
    ;;

run_initial_setup_or_perform_upgrade)
    initial_setup_or_perform_upgrade
    ;;

run_tests)
    initial_setup_or_perform_upgrade
    shift
    exec runuser --user mayan -- /usr/local/bin/run_tests.sh "${@}"
    ;;

run_worker)
    shift
    exec runuser --user mayan -- /usr/local/bin/run_worker.sh "${@}"
    ;;

*)
    "${@}"
    ;;

esac
