#!/bin/bash
# Install an Egyptian / Mayan EDMS custom app into a running Docker stack.
# Run from the directory containing your docker-compose.yml.
#
# Usage:
#   bash install-custom-apps.sh /path/to/app-directory
#
# The app directory must contain apps.py with a MayanAppConfig subclass.
# The Python packages listed in its requirements.txt, if any, are installed in
# every Mayan container (MAYAN_PIP_INSTALLS).
set -e

APP_DIR="${1:-}"

if [ -z "$APP_DIR" ]; then
    echo "Usage: bash install-custom-apps.sh /path/to/app-directory" >&2
    exit 1
fi

APP_DIR="$(cd "$APP_DIR" && pwd)"

if [ ! -f "$APP_DIR/apps.py" ]; then
    echo "Error: apps.py not found in $APP_DIR." >&2
    exit 1
fi

APP_MODULE=$(grep -m1 "^\s*name\s*=" "$APP_DIR/apps.py" \
    | sed "s/.*=\s*['\"]//;s/['\"].*//")
APP_CLASS=$(grep -m1 "^class.*MayanAppConfig" "$APP_DIR/apps.py" \
    | sed 's/class \([A-Za-z_]*\).*/\1/')

if [ -z "$APP_MODULE" ] || [ -z "$APP_CLASS" ]; then
    echo "Error: could not detect app module or AppConfig class from $APP_DIR/apps.py." >&2
    echo "Make sure apps.py defines 'name = ...' and a class extending MayanAppConfig." >&2
    exit 1
fi

THIS_APP="${APP_MODULE}.apps.${APP_CLASS}"
APP_SLUG=$(echo "$APP_MODULE" | awk -F. '{print $NF}')
INSTALL_DIR="/opt/mayan-${APP_SLUG}"

# Python packages needed by the registered apps (requirements.txt of each
# app). They go into MAYAN_PIP_INSTALLS: the Mayan image installs them with
# pip at every start of every container, before Mayan itself, so they survive
# the re-creation of the containers and reach the workers too. Mayan 4.10
# runs that pip command through a shell: a line must not contain quotes,
# < > or other shell characters, nor spaces except after a pip option.
PIP_INSTALLS=""

pip_installs_add() {
    case " ${PIP_INSTALLS} " in
        *" $1 "*) ;;
        *) PIP_INSTALLS="${PIP_INSTALLS:+${PIP_INSTALLS} }$1" ;;
    esac
}

requirements_add() {
    local line
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        line="${line%%[[:space:]]#*}"
        line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        case "$line" in
            ''|'#'*) continue ;;
            *[\'\"\<\>\|\&\;\$\`\(\)\{\}\*\?\[\]\\]* | -*[[:space:]]*[[:space:]]* | [!-]*[[:space:]]*)
                echo "Error: unsupported line in $1:" >&2
                echo "  $line" >&2
                echo "One requirement per line, without quotes, spaces or < > (use == or ~=)." >&2
                exit 1
                ;;
        esac
        pip_installs_add "$line"
    done < "$1"
}

# Check the requirements of this app before changing anything.
if [ -f "$APP_DIR/requirements.txt" ]; then
    requirements_add "$APP_DIR/requirements.txt"
fi


echo "=== Mayan EDMS — Installing ${APP_MODULE} ==="
echo ""

# Detect docker compose command
if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null 2>&1; then
    DC="docker-compose"
else
    echo "Error: docker compose is not available." >&2
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "Error: run this script from the directory containing your docker-compose.yml." >&2
    echo "Usage: cd /path/to/docker-compose && bash install-custom-apps.sh /path/to/${APP_SLUG}" >&2
    exit 1
fi

# Find the running Mayan app container
echo "Detecting Mayan app container..."
CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '[-_]app[-_]?[0-9]*$' | head -1)
if [ -z "$CONTAINER" ]; then
    echo "Error: no running Mayan app container found." >&2
    echo ""
    echo "Running containers:"
    docker ps --format '  {{.Names}}'
    echo ""
    echo "Make sure your Mayan containers are running: $DC up -d"
    exit 1
fi
echo "  → $CONTAINER"
echo ""

# Detect site-packages directory
echo "Detecting Python environment..."
SITE=$(docker exec "$CONTAINER" \
    find /opt /home /usr/local -name "site-packages" -type d 2>/dev/null \
    | head -1 | tr -d '\r')

if [ -z "$SITE" ] || [[ "$SITE" != /* ]]; then
    echo "Error: could not detect Python site-packages path in container '$CONTAINER'." >&2
    echo ""
    echo "Run the following to diagnose:" >&2
    echo "  docker exec $CONTAINER find /opt /home /usr/local -name site-packages -type d 2>/dev/null" >&2
    exit 1
fi
echo "  → $SITE"
echo ""

MOUNT_TARGET="${SITE}/mayan/apps/${APP_SLUG}"

# Find the mayan-edms command inside the container (in a bin directory: the
# 4.12 image also has static files named mayan-edms.*.ttf.gz).
MAYAN_CMD=$(docker exec "$CONTAINER" \
    find /opt /usr/local -path "*/bin/mayan-edms*" -not -name "*.pyc" -type f 2>/dev/null \
    | head -1 | tr -d '\r')
if [ -z "$MAYAN_CMD" ]; then
    echo "Error: could not find mayan-edms executable in container." >&2
    exit 1
fi

# Copy app files to install directory
echo "Copying app files to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -r "$APP_DIR/." "$INSTALL_DIR/"

# Registry: one line per installed app — CLASS_PATH|INSTALL_DIR|MOUNT_TARGET
# Kept alongside docker-compose.yml so all installs share it.
REGISTRY="$(pwd)/.mayan-apps"
touch "$REGISTRY"

if grep -qF "${THIS_APP}|" "$REGISTRY"; then
    echo "Note: ${THIS_APP} already registered — updating files only."
    echo ""
fi

# Update registry: remove old entry for this app, add current one.
# grep -vF exits 1 when no lines remain — separate || true so mv always runs.
{ grep -vF "${THIS_APP}|" "$REGISTRY" || true; } > "$REGISTRY.tmp"
mv "$REGISTRY.tmp" "$REGISTRY"
echo "${THIS_APP}|${INSTALL_DIR}|${MOUNT_TARGET}" >> "$REGISTRY"

# Build merged app list from the full registry
FINAL_APPS=$(cut -d'|' -f1 "$REGISTRY" | sort | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')

# Keep the packages already set by the docker-compose.yml/.env of the user.
USER_PIP_INSTALLS=$($DC -f docker-compose.yml config 2>/dev/null \
    | sed -n 's/^[[:space:]]*MAYAN_PIP_INSTALLS:[[:space:]]*//p' | head -1)
USER_PIP_INSTALLS="${USER_PIP_INSTALLS#[\"\']}"
USER_PIP_INSTALLS="${USER_PIP_INSTALLS%[\"\']}"
PIP_INSTALLS="$USER_PIP_INSTALLS"

while IFS='|' read -r cls dir mnt; do
    if [ -f "${dir}/requirements.txt" ]; then
        requirements_add "${dir}/requirements.txt"
    fi
done < "$REGISTRY"

# Waits until the Mayan entrypoint of the app container has done its setup,
# pip installs included (the first start after adding packages can take
# several minutes). Mayan 4.11+ then prints "Executing final target"; 4.10
# runs "fc-cache -v" right after pip.
wait_for_app_setup() {
    local container started
    echo "Waiting for the app container to finish its setup (Python packages included)..."
    for i in $(seq 1 360); do
        container=$($DC ps -q app 2>/dev/null | head -1)
        if [ -n "$container" ]; then
            started=$(docker inspect --format '{{.State.StartedAt}}' "$container" 2>/dev/null || true)
            if [ -n "$started" ] && docker logs --since "$started" "$container" 2>&1 \
                | grep -qE 'Executing final target|fc-cache: succeeded'; then
                return 0
            fi
        fi
        sleep 5
    done
    echo "Warning: the app container did not finish its setup in 30 minutes; see: $DC logs app" >&2
}

# Back up any existing override
if [ -f "docker-compose.override.yml" ]; then
    cp "docker-compose.override.yml" "docker-compose.override.yml.bak"
    echo "Existing docker-compose.override.yml backed up to docker-compose.override.yml.bak"
    echo ""
fi

SKIP="postgresql|postgres|mysql|rabbitmq|redis|elasticsearch|traefik|flower|postgresql-backup"

# ALL_SERVICES: every Mayan service defined for the active profiles (including
# workers and beat in multi-container mode). Used to write the override so that
# services get the volume even if they are not currently running.
ALL_SERVICES=$($DC config --services 2>/dev/null | grep -vE "^($SKIP)$" || true)

# RUNNING_SERVICES: only currently running containers — used for --force-recreate.
RUNNING_SERVICES=$($DC ps --services 2>/dev/null | grep -vE "^($SKIP)$" || true)

if [ -z "$ALL_SERVICES" ]; then
    echo "Error: no Mayan services found in this docker-compose project." >&2
    exit 1
fi

if [ -z "$RUNNING_SERVICES" ]; then
    echo "Error: no running Mayan containers found. Start the stack first: $DC up -d" >&2
    exit 1
fi

# Celery queues of the apps for the custom worker of Mayan's docker-compose.yml
# (see below); start with the list of the previous run, if any.
CUSTOM_WORKER=worker_custom_queue
CUSTOM_QUEUES=$(sed -n 's/^ *MAYAN_QUEUE_LIST: *"\(.*\)"$/\1/p' \
    docker-compose.override.yml 2>/dev/null | head -1)

# Generate docker-compose.override.yml — volumes for ALL registered apps,
# entries for ALL defined services (not just running ones).
write_override() {
    local services="$ALL_SERVICES"
    if [ -n "$CUSTOM_QUEUES" ] && ! printf '%s\n' "$services" | grep -qx "$CUSTOM_WORKER"; then
        services="$services $CUSTOM_WORKER"
    fi

    cat > docker-compose.override.yml << YAML
# Generated by install-custom-apps.sh — do not edit manually.
# Re-run the script to update. Registry: .mayan-apps
services:
YAML

    for SERVICE in $services; do
        echo "  ${SERVICE}:" >> docker-compose.override.yml
        if [ "$SERVICE" = "$CUSTOM_WORKER" ] && [ -n "$CUSTOM_QUEUES" ]; then
            # Enabled without its profile (extra_worker_custom).
            echo "    profiles: !reset []" >> docker-compose.override.yml
        fi
        echo "    volumes:" >> docker-compose.override.yml
        while IFS='|' read -r cls dir mnt; do
            echo "      - \"${dir}:${mnt}\"" >> docker-compose.override.yml
        done < "$REGISTRY"
        printf "    environment:\n      MAYAN_COMMON_EXTRA_APPS: \"[%s]\"\n" \
            "$FINAL_APPS" >> docker-compose.override.yml
        if [ -n "$PIP_INSTALLS" ]; then
            # YAML double quotes; $$ keeps a literal $ from compose interpolation.
            printf "      MAYAN_PIP_INSTALLS: \"%s\"\n" \
                "$(printf '%s' "$PIP_INSTALLS" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\$/$$/g')" \
                >> docker-compose.override.yml
        fi
        if [ "$SERVICE" = "$CUSTOM_WORKER" ] && [ -n "$CUSTOM_QUEUES" ]; then
            printf "      MAYAN_QUEUE_LIST: \"%s\"\n" "$CUSTOM_QUEUES" >> docker-compose.override.yml
        fi
    done
}

echo "Generating docker-compose.override.yml ..."
write_override

echo "  Apps registered: $FINAL_APPS"
echo "  Python packages (MAYAN_PIP_INSTALLS): ${PIP_INSTALLS:-none}"
echo "  Services in override: $ALL_SERVICES"
echo "  Services restarted:   $RUNNING_SERVICES"
echo ""

# Recreate containers to apply new volumes and environment variables from the override
echo "Applying new configuration (recreating containers)..."
$DC up -d

# Migrations and collectstatic import every app: wait for the Python packages.
wait_for_app_setup

echo "Delete bootswatch docs directory to mitigate the collectstatic problem"
$DC exec -T app rm -rf "${SITE}/mayan/apps/appearance_bootstrap/static/appearance_bootstrap/node_modules/bootswatch/docs/"

# Run migrations — Django warns about DB access during app init which can
# produce a non-zero exit code even on success; continue regardless.
echo "Running database migrations..."
$DC exec -T app "$MAYAN_CMD" migrate || true

# Rebuild static files manifest.
# --ignore node_modules avoids a known WhiteNoise failure on bootswatch CSS
# files that reference paths with spaces/parentheses.
echo "Collecting static files..."
$DC exec -T app "$MAYAN_CMD" collectstatic --noinput

# In the all-in-one container the workers listen to fixed queue lists (its
# supervisord configuration): the queues of the apps would have no worker.
# They go to the custom worker of Mayan's docker-compose.yml
# (worker_custom_queue), enabled by the override without its profile; the
# queues already set by the user (MAYAN_WORKER_CUSTOM_QUEUE_LIST) are kept.
SUPERVISORD_CONF="/etc/supervisor/conf.d/mayan-edms.conf"
PREVIOUS_CUSTOM_QUEUES="$CUSTOM_QUEUES"
APP_QUEUES=""
CUSTOM_QUEUES=""
if $DC exec -T app test -f "$SUPERVISORD_CONF" 2>/dev/null; then
    ALL_QUEUES=$($DC exec -T app "$MAYAN_CMD" shell -c \
        "from mayan.apps.task_manager.classes import CeleryQueue; print(chr(10).join(queue.name for queue in CeleryQueue.all()))" \
        2>/dev/null | tr -d '\r' | grep -E '^[A-Za-z0-9_.-]+$' | sort -u || true)
    SERVED_QUEUES=$($DC exec -T app cat "$SUPERVISORD_CONF" | tr -d '\r' \
        | grep -o -- '--queues=[^ "]*' | cut -d= -f2 | tr ',' '\n' | sort -u)
    APP_QUEUES=$(printf '%s\n' "$ALL_QUEUES" | grep -vxF -f <(printf '%s\n' "$SERVED_QUEUES") || true)
fi
if [ -n "$APP_QUEUES" ] \
    && $DC --profile extra_worker_custom config --services 2>/dev/null | grep -qx "$CUSTOM_WORKER"; then
    USER_CUSTOM_QUEUES=$($DC -f docker-compose.yml --profile extra_worker_custom config 2>/dev/null \
        | sed -n 's/^[[:space:]]*MAYAN_QUEUE_LIST:[[:space:]]*//p' | head -1)
    USER_CUSTOM_QUEUES="${USER_CUSTOM_QUEUES#[\"\']}"
    USER_CUSTOM_QUEUES="${USER_CUSTOM_QUEUES%[\"\']}"
    # Celery refuses to start with a queue unknown to Mayan: it would stop
    # the worker of the apps too.
    USER_CUSTOM_QUEUES=$(printf '%s' "$USER_CUSTOM_QUEUES" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$' || true)
    UNKNOWN_QUEUES=$(printf '%s\n' "$USER_CUSTOM_QUEUES" | grep -vxF -f <(printf '%s\n' "$ALL_QUEUES") || true)
    if [ -n "$UNKNOWN_QUEUES" ]; then
        echo "Warning: MAYAN_WORKER_CUSTOM_QUEUE_LIST has queues unknown to Mayan, left out:" \
            $UNKNOWN_QUEUES >&2
    fi
    CUSTOM_QUEUES=$(printf '%s\n' $USER_CUSTOM_QUEUES $APP_QUEUES \
        | grep -xF -f <(printf '%s\n' "$ALL_QUEUES") | awk '!seen[$0]++' | paste -sd, -)
fi

if [ "$CUSTOM_QUEUES" != "$PREVIOUS_CUSTOM_QUEUES" ]; then
    # "profiles: !reset" needs Docker Compose 2.24 or later (like the
    # docker-compose.yml of Mayan 4.12).
    COMPOSE_VERSION=$($DC version --short 2>/dev/null | sed 's/^v//')
    if [ -n "$CUSTOM_QUEUES" ] && ! printf '%s\n2.24\n' "$COMPOSE_VERSION" | sort -V -C -r 2>/dev/null; then
        echo "Warning: Docker Compose ${COMPOSE_VERSION:-unknown} is older than 2.24: the queues" >&2
        echo "  $CUSTOM_QUEUES" >&2
        echo "have no worker. Enable the extra_worker_custom profile and set" >&2
        echo "MAYAN_WORKER_CUSTOM_QUEUE_LIST to them in your .env." >&2
        CUSTOM_QUEUES="$PREVIOUS_CUSTOM_QUEUES"
    else
        echo "Celery queues of the apps for the $CUSTOM_WORKER container: ${CUSTOM_QUEUES:-none}"
        write_override
        $DC up -d
    fi
fi

# Restart so Django reloads the static files manifest written by collectstatic
echo "Restarting app to reload static files manifest..."
$DC stop
$DC start

# Wait for app to be ready before regenerating supervisor config (the
# entrypoint runs pip again at every start).
wait_for_app_setup

# Regenerate supervisord configuration so new Celery queues from custom apps
# are registered with their workers. platforms_template docker_supervisord
# runs Django (which loads MAYAN_COMMON_EXTRA_APPS) and builds the --queues
# list dynamically from all registered CeleryQueue objects.
# This applies to single-container mode (supervisord manages all workers).
# In multi-container mode the individual worker containers already restarted
# above with the updated MAYAN_COMMON_EXTRA_APPS — run_worker.sh discovers
# queues at that point.
# Detect single-container mode by checking if the supervisord conf file
# exists in the container — it is created by the Mayan entrypoint only in
# single-container mode. supervisorctl checks are unreliable here because
# programs may still be starting (exit 3) or the socket path may vary.
if [ -n "$CUSTOM_QUEUES" ]; then
    echo "The queues of the apps are served by the $CUSTOM_WORKER container: $CUSTOM_QUEUES"
elif $DC exec -T app test -f "$SUPERVISORD_CONF" 2>/dev/null; then
    # Mayan 4.12+ images have no docker_supervisord template (fixed queue
    # lists, see the custom worker above).
    if $DC exec -T app "$MAYAN_CMD" platforms_template --list 2>/dev/null \
        | grep -q "docker_supervisord"; then
        echo "Regenerating supervisord configuration to register new Celery queues..."
        # -u root: writing /etc/supervisor/conf.d/ requires root; docker compose
        # exec runs as the container user (mayan) by default. Written to a
        # temporary file first: a failure must not leave an empty configuration,
        # Mayan would not start at the next restart of the container.
        if $DC exec -T -u root app sh -c \
            "'$MAYAN_CMD' platforms_template docker_supervisord \
             > /tmp/mayan-edms.conf.new \
             && test -s /tmp/mayan-edms.conf.new \
             && mv /tmp/mayan-edms.conf.new '$SUPERVISORD_CONF' \
             && supervisorctl reread \
             && supervisorctl update"; then
            echo "Supervisord updated."
        else
            echo "Warning: supervisord config update failed — restart the stack manually to apply new queues."
        fi
    elif [ -n "$APP_QUEUES" ]; then
        echo "Warning: no worker listens to the queues of the apps:" $APP_QUEUES >&2
    fi
else
    echo "Multi-container mode detected — worker containers restarted with new queue list."
fi

echo ""
echo "=== Installation complete: ${APP_MODULE} ==="
echo ""

echo "Next step: grant permissions in Setup → Roles."
