#!/bin/bash
# Install an Egyptian / Mayan EDMS custom app into a running Docker stack.
# Run from the directory containing your docker-compose.yml.
#
# Usage:
#   bash install-custom-apps.sh /path/to/app-directory
#
# The app directory must contain apps.py with a MayanAppConfig subclass.
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

# Find the mayan-edms command inside the container
MAYAN_CMD=$(docker exec "$CONTAINER" \
    find /opt /usr/local -name "mayan-edms*" -not -name "*.pyc" -type f 2>/dev/null \
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

# Generate docker-compose.override.yml — volumes for ALL registered apps,
# entries for ALL defined services (not just running ones).
echo "Generating docker-compose.override.yml ..."
cat > docker-compose.override.yml << YAML
# Generated by install-custom-apps.sh — do not edit manually.
# Re-run the script to update. Registry: .mayan-apps
services:
YAML

for SERVICE in $ALL_SERVICES; do
    echo "  ${SERVICE}:" >> docker-compose.override.yml
    echo "    volumes:" >> docker-compose.override.yml
    while IFS='|' read -r cls dir mnt; do
        echo "      - \"${dir}:${mnt}\"" >> docker-compose.override.yml
    done < "$REGISTRY"
    printf "    environment:\n      MAYAN_COMMON_EXTRA_APPS: \"[%s]\"\n" \
        "$FINAL_APPS" >> docker-compose.override.yml
done

echo "  Apps registered: $FINAL_APPS"
echo "  Services in override: $ALL_SERVICES"
echo "  Services restarted:   $RUNNING_SERVICES"
echo ""

# Recreate containers to apply new volumes and environment variables from the override
echo "Applying new configuration (recreating containers)..."
$DC up -d

# Wait for the app container to accept exec commands before continuing
echo "Waiting for app container to be ready..."
for i in $(seq 1 30); do
    if $DC exec -T app true 2>/dev/null; then
        break
    fi
    sleep 3
done

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

# Restart so Django reloads the static files manifest written by collectstatic
echo "Restarting app to reload static files manifest..."
$DC stop
$DC start

# Wait for app to be ready before regenerating supervisor config
echo "Waiting for app container to be ready (supervisor update)..."
for i in $(seq 1 30); do
    if $DC exec -T app true 2>/dev/null; then
        break
    fi
    sleep 3
done

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
SUPERVISORD_CONF="/etc/supervisor/conf.d/mayan-edms.conf"
if $DC exec -T app test -f "$SUPERVISORD_CONF" 2>/dev/null; then
    echo "Regenerating supervisord configuration to register new Celery queues..."
    # -u root: writing /etc/supervisor/conf.d/ requires root; docker compose
    # exec runs as the container user (mayan) by default.
    $DC exec -T -u root app sh -c \
        "'$MAYAN_CMD' platforms_template docker_supervisord \
         > '$SUPERVISORD_CONF' \
         && supervisorctl reread \
         && supervisorctl update" \
        || echo "Warning: supervisord config update failed — restart the stack manually to apply new queues."
    echo "Supervisord updated."
else
    echo "Multi-container mode detected — worker containers restarted with new queue list."
fi

echo ""
echo "=== Installation complete: ${APP_MODULE} ==="
echo ""

echo "Next step: grant permissions in Setup → Roles."
