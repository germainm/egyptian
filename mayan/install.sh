#!/bin/bash
# Egyptian (Mayan EDMS) - Script d'installation sans Docker sur Debian 12
# Usage: sudo ./install.sh

set -euo pipefail

# ---- Vérification root ----
if [[ $EUID -ne 0 ]]; then
    echo "Ce script doit être exécuté en tant que root : sudo $0"
    exit 1
fi

# ---- Vérification sudo ----
if ! command -v sudo &>/dev/null; then
    echo "Erreur: sudo est requis mais n'est pas installé."
    echo "Installez-le avec : apt install sudo"
    exit 1
fi

# ---- Vérification git ----
if ! command -v git &>/dev/null; then
    echo "Installation de git..."
    apt-get update -q
    apt-get install --yes git
fi

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
APP_DIR="/opt/egyptian"
APP_USER="egyptian"
VENV_DIR="$APP_DIR/venv"
MEDIA_DIR="$APP_DIR/media"
SUPERVISOR_CONF="/etc/supervisor/conf.d/egyptian.conf"
CONFIG_YML="$MEDIA_DIR/config.yml"

# ---- Copie du code source ----
echo "Copie du code source vers $APP_DIR..."
mkdir -p "$APP_DIR"
cp -r "$SCRIPT_DIR/." "$APP_DIR/"
mkdir -p "$APP_DIR/requirements"
cp -r "$SCRIPT_DIR/../requirements/." "$APP_DIR/requirements/"

echo ""
echo "=========================================="
echo "  Egyptian (Mayan EDMS) - Installation"
echo "=========================================="
echo ""
echo "Répondez aux questions. Entrée = valeur par défaut."
echo "Note: évitez les caractères spéciaux (\", ', \$, \`) dans les mots de passe."
echo ""

# ---- PostgreSQL ----
echo "--- PostgreSQL ---"
read -p  "  Nom de la base de données  [egyptian] : " DB_NAME;     DB_NAME=${DB_NAME:-egyptian}
read -p  "  Utilisateur                [egyptian] : " DB_USER;     DB_USER=${DB_USER:-egyptian}
read -sp "  Mot de passe                          : " DB_PASSWORD;  echo
read -p  "  Hôte                       [127.0.0.1]: " DB_HOST;     DB_HOST=${DB_HOST:-127.0.0.1}

echo ""
echo "--- RabbitMQ ---"
read -p  "  Utilisateur                [egyptian] : " RABBITMQ_USER;     RABBITMQ_USER=${RABBITMQ_USER:-egyptian}
read -sp "  Mot de passe                          : " RABBITMQ_PASSWORD;  echo
read -p  "  VHost                      [egyptian] : " RABBITMQ_VHOST;    RABBITMQ_VHOST=${RABBITMQ_VHOST:-egyptian}
read -p  "  Hôte                       [127.0.0.1]: " RABBITMQ_HOST;     RABBITMQ_HOST=${RABBITMQ_HOST:-127.0.0.1}
read -p  "  Port                       [5672]     : " RABBITMQ_PORT;     RABBITMQ_PORT=${RABBITMQ_PORT:-5672}

echo ""
echo "--- Redis ---"
read -sp "  Mot de passe                          : " REDIS_PASSWORD; echo
read -p  "  Hôte                       [127.0.0.1]: " REDIS_HOST;    REDIS_HOST=${REDIS_HOST:-127.0.0.1}
read -p  "  Port                       [6379]     : " REDIS_PORT;    REDIS_PORT=${REDIS_PORT:-6379}

echo ""
echo "--- Elasticsearch (optionnel) ---"
read -p "  Activer Elasticsearch ? (o/n)      [n] : " ES_ENABLE; ES_ENABLE=${ES_ENABLE:-n}
ES_SUPERVISOR_LINES=""
if [[ "$ES_ENABLE" =~ ^[oO]$ ]]; then
    read -p  "  URL (ex: https://es.exemple.com)      : " ES_URL
    read -p  "  Port                       [9200]     : " ES_PORT;     ES_PORT=${ES_PORT:-9200}
    read -p  "  Utilisateur                           : " ES_USER
    read -sp "  Mot de passe                          : " ES_PASSWORD; echo
    read -p  "  Vérifier les certificats SSL ? (o/n) [n]: " ES_VERIFY; ES_VERIFY=${ES_VERIFY:-n}
    if [[ "$ES_VERIFY" =~ ^[oO]$ ]]; then ES_VERIFY_BOOL="true"; else ES_VERIFY_BOOL="false"; fi
    ES_SUPERVISOR_LINES="    MAYAN_SEARCH_BACKEND=\"mayan.apps.dynamic_search.backends.elasticsearch.ElasticsearchSearchBackend\",
    MAYAN_SEARCH_BACKEND_ARGUMENTS=\"{client_kwargs: {basic_auth: [$ES_USER, $ES_PASSWORD], hosts: '$ES_URL:$ES_PORT', verify_certs: $ES_VERIFY_BOOL}, search_page_size: 500}\","
fi

echo ""
echo "--- OIDC (optionnel) ---"
read -p "  Activer l'authentification OIDC ? (o/n) [n]: " OIDC_ENABLE; OIDC_ENABLE=${OIDC_ENABLE:-n}
OIDC_USER_PROFILE_URL=""
if [[ "$OIDC_ENABLE" =~ ^[oO]$ ]]; then
    read -p "  URL du profil utilisateur OIDC        : " OIDC_USER_PROFILE_URL
fi

echo ""
echo "--- Nginx + SSL (optionnel) ---"
read -p "  Configurer Nginx avec SSL ? (o/n)  [n] : " NGINX_ENABLE; NGINX_ENABLE=${NGINX_ENABLE:-n}
DOMAIN_NAME=""
CERTBOT_EMAIL=""
if [[ "$NGINX_ENABLE" =~ ^[oO]$ ]]; then
    read -p "  Nom de domaine (ex: mon.domaine.com)  : " DOMAIN_NAME
    read -p "  Email pour Let's Encrypt              : " CERTBOT_EMAIL
fi

echo ""
echo "--- Paramètres généraux ---"
read -p "  Fuseau horaire [America/Montreal]     : " TIMEZONE;     TIMEZONE=${TIMEZONE:-America/Montreal}
read -p "  Hôte autorisé - IP ou domaine    [*]  : " ALLOWED_HOST; ALLOWED_HOST=${ALLOWED_HOST:-"*"}

echo ""
echo "=========================================="
echo "  Démarrage de l'installation..."
echo "=========================================="

# ---- Paquets système ----
echo "[1/10] Installation des paquets système..."
apt-get update -q
apt-get install --yes ca-certificates fonts-arphic-uming \
    fonts-arphic-ukai fonts-unfonts-core gcc gnupg1 graphviz libfuse2 \
    libarchive-zip-perl libimage-exiftool-perl libmagic1 \
    libreoffice-calc-nogui libreoffice-draw-nogui libreoffice-impress-nogui \
    libreoffice-math-nogui libreoffice-writer-nogui libfile-mimeinfo-perl \
    libldap-2.5-0 libldap-dev libpq-dev libpq5 libsasl2-dev libsasl2-2 \
    poppler-utils postgresql python3-dev python3-venv rabbitmq-server \
    redis-server sane-utils supervisor tesseract-ocr

# ---- Utilisateur système ----
echo "[2/10] Création de l'utilisateur $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
    adduser "$APP_USER" --disabled-password --disabled-login --gecos ""
fi

# ---- Venv & dépendances Python ----
echo "[3/10] Création de l'environnement virtuel Python..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements/production.txt"
"$VENV_DIR/bin/pip" install --quiet psycopg2 pyotp redis

PYTHON_VERSION=$("$VENV_DIR/bin/python3" -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
ln -sf "$APP_DIR" "$VENV_DIR/lib/$PYTHON_VERSION/site-packages/mayan"
ln -sf /usr/bin/python3 /usr/bin/python 2>/dev/null || true

# ---- RabbitMQ ----
echo "[4/10] Configuration de RabbitMQ..."
rabbitmqctl add_user "$RABBITMQ_USER" "$RABBITMQ_PASSWORD" 2>/dev/null || \
    rabbitmqctl change_password "$RABBITMQ_USER" "$RABBITMQ_PASSWORD"
rabbitmqctl add_vhost "$RABBITMQ_VHOST" 2>/dev/null || true
rabbitmqctl set_permissions -p "$RABBITMQ_VHOST" "$RABBITMQ_USER" ".*" ".*" ".*"

# ---- PostgreSQL ----
echo "[5/10] Configuration de PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH password '$DB_PASSWORD';" 2>/dev/null || \
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH password '$DB_PASSWORD';"
sudo -u postgres createdb -O "$DB_USER" "$DB_NAME" 2>/dev/null || true

# ---- Redis ----
echo "[6/10] Configuration de Redis..."
if grep -q "^requirepass" /etc/redis/redis.conf 2>/dev/null; then
    sed -i "s/^requirepass .*/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
else
    printf '\nmaxmemory-policy allkeys-lru\nsave ""\ndatabases 3\nrequirepass %s\n' \
        "$REDIS_PASSWORD" >> /etc/redis/redis.conf
fi
systemctl restart redis
# Attendre que Redis soit prêt et vérifier que le mot de passe est actif
for i in {1..10}; do
    if redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG; then
        break
    fi
    sleep 1
done

# ---- Génération du fichier Supervisor ----
echo "[7/10] Génération de la configuration Supervisor..."

cat > "$SUPERVISOR_CONF" << SUPERVISOREOF

[supervisord]
environment=
    PYTHONPATH="$MEDIA_DIR/user_settings",
    MAYAN_ALLOWED_HOSTS='["$ALLOWED_HOST"]',
    MAYAN_MEDIA_ROOT="$MEDIA_DIR/",
    MAYAN_PYTHON_BIN_DIR=$VENV_DIR/bin/,
    MAYAN_GUNICORN_BIN=$VENV_DIR/bin/gunicorn,
    MAYAN_GUNICORN_LIMIT_REQUEST_LINE=4094,
    MAYAN_GUNICORN_MAX_REQUESTS=500,
    MAYAN_GUNICORN_REQUESTS_JITTER=50,
    MAYAN_GUNICORN_TEMPORARY_DIRECTORY="",
    MAYAN_GUNICORN_TIMEOUT=120,
    MAYAN_GUNICORN_WORKER_CLASS=gevent,
    MAYAN_GUNICORN_WORKERS=5,
    MAYAN_SETTINGS_MODULE=mayan.settings.production,
    MAYAN_SUPERVISOR_AUTORESTART=true,
    MAYAN_DATABASES="{'default':{'ENGINE':'django.db.backends.postgresql','HOST':'$DB_HOST','NAME':'$DB_NAME','PASSWORD':'$DB_PASSWORD','USER':'$DB_USER'}}",
    MAYAN_CELERY_BROKER_LOGIN_METHOD="AMQPLAIN",
    MAYAN_CELERY_BROKER_URL="amqp://$RABBITMQ_USER:$RABBITMQ_PASSWORD@$RABBITMQ_HOST:$RABBITMQ_PORT/$RABBITMQ_VHOST",
    MAYAN_CELERY_RESULT_BACKEND="redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/1",
    MAYAN_LOCK_MANAGER_BACKEND="mayan.apps.lock_manager.backends.redis_lock.RedisLock",
    MAYAN_LOCK_MANAGER_BACKEND_ARGUMENTS="{'redis_url':'redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/2'}",
    MAYAN_WORKER_A_CONCURRENCY="--concurrency=4",
    MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_A_MAX_TASKS_PER_CHILD="--max-tasks-per-child=4000",
    MAYAN_WORKER_B_CONCURRENCY="--concurrency=6",
    MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_B_MAX_TASKS_PER_CHILD="--max-tasks-per-child=4000",
    MAYAN_WORKER_C_CONCURRENCY="--concurrency=2",
    MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_C_MAX_TASKS_PER_CHILD="--max-tasks-per-child=1000",
    MAYAN_WORKER_D_CONCURRENCY="--concurrency=4",
    MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_D_MAX_TASKS_PER_CHILD="--max-tasks-per-child=500",
    MAYAN_WORKER_E_CONCURRENCY="--concurrency=4",
    MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_E_MAX_TASKS_PER_CHILD="--max-tasks-per-child=20000",
    MAYAN_WORKER_F_CONCURRENCY="--concurrency=4",
    MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD="--max-memory-per-child=500000",
    MAYAN_WORKER_F_MAX_TASKS_PER_CHILD="--max-tasks-per-child=4000",
$(if [[ -n "$ES_SUPERVISOR_LINES" ]]; then echo "$ES_SUPERVISOR_LINES"; fi)
    _LAST_LINE=""

[program:mayan-edms-gunicorn]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = %(ENV_MAYAN_GUNICORN_BIN)s --bind 0.0.0.0:8000 --env DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s --limit-request-line %(ENV_MAYAN_GUNICORN_LIMIT_REQUEST_LINE)s --max-requests %(ENV_MAYAN_GUNICORN_MAX_REQUESTS)s --max-requests-jitter %(ENV_MAYAN_GUNICORN_REQUESTS_JITTER)s %(ENV_MAYAN_GUNICORN_TEMPORARY_DIRECTORY)s --worker-class %(ENV_MAYAN_GUNICORN_WORKER_CLASS)s --timeout %(ENV_MAYAN_GUNICORN_TIMEOUT)s --workers %(ENV_MAYAN_GUNICORN_WORKERS)s mayan.wsgi
environment = DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
redirect_stderr = true
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_a]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 0 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_A_CONCURRENCY)s --hostname=mayan-edms-worker_a.%%h --loglevel=ERROR -Ofair --queues=converter,events_fast %(ENV_MAYAN_WORKER_A_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_A_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_b]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 2 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_B_CONCURRENCY)s --hostname=mayan-edms-worker_b.%%h --loglevel=ERROR -Ofair --queues=documents_fast,documents_file,documents_file_slow,documents_slow,documents_version,file_caching,indexing,metadata,parsing,sources,storage,workflows,itineraires %(ENV_MAYAN_WORKER_B_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_B_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_c]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 10 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_C_CONCURRENCY)s --hostname=mayan-edms-worker_c.%%h --loglevel=ERROR -Ofair --queues=checkouts_periodic,documents_downloads,documents_exports,documents_periodic,documents_trash,duplicates,duplicates_slow,events_slow,file_caching_slow,indexing_slow,mailing,signatures,sources_periodic,statistics,workflows_slow %(ENV_MAYAN_WORKER_C_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_C_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_d]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 15 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_D_CONCURRENCY)s --hostname=mayan-edms-worker_d.%%h --loglevel=ERROR -Ofair --queues=file_metadata,ocr,signatures_slow,storage_periodic %(ENV_MAYAN_WORKER_D_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_D_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_e]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 2 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_E_CONCURRENCY)s --hostname=mayan-edms-worker_e.%%h --loglevel=ERROR -Ofair --queues=search,search_slow %(ENV_MAYAN_WORKER_E_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_E_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-worker_f]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 0 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan worker %(ENV_MAYAN_WORKER_F_CONCURRENCY)s --hostname=mayan-edms-worker_f.%%h --loglevel=ERROR -Ofair --queues=converter %(ENV_MAYAN_WORKER_F_MAX_MEMORY_PER_CHILD)s %(ENV_MAYAN_WORKER_F_MAX_TASKS_PER_CHILD)s",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER

[program:mayan-edms-celery-beat]
autorestart = %(ENV_MAYAN_SUPERVISOR_AUTORESTART)s
autostart = true
command = nice -n 1 %(ENV_COMMAND)s
environment =
  COMMAND="%(ENV_MAYAN_PYTHON_BIN_DIR)scelery -A mayan beat --pidfile= -l ERROR",
  DJANGO_SETTINGS_MODULE=%(ENV_MAYAN_SETTINGS_MODULE)s
killasgroup = true
numprocs = 1
priority = 998
startsecs = 10
stopwaitsecs = 1
user = $APP_USER
directory = /home/$APP_USER
SUPERVISOREOF

chmod 640 "$SUPERVISOR_CONF"
chown root:root "$SUPERVISOR_CONF"

# ---- Génération du config.yml ----
echo "[8/10] Génération du fichier config.yml..."
mkdir -p "$MEDIA_DIR"

cat > "$CONFIG_YML" << CONFIGEOF
ALLOWED_HOSTS:
- '$ALLOWED_HOST'
TIME_ZONE: $TIMEZONE
CONFIGEOF

if [[ "$OIDC_ENABLE" =~ ^[oO]$ ]]; then
    cat >> "$CONFIG_YML" << OIDCEOF
AUTHENTICATION_BACKEND: mayan.apps.authentication.authentication_backends.AuthenticationBackendModelDjangoOIDC
AUTHENTICATION_OIDC_USER_PROFILE_URL: '$OIDC_USER_PROFILE_URL'
OIDCEOF
fi

chown "$APP_USER:$APP_USER" "$CONFIG_YML"

# ---- Initialisation de l'application ----
echo "[9/10] Initialisation de l'application..."
chown -R "$APP_USER" "$APP_DIR"

sudo -u "$APP_USER" \
    DJANGO_SETTINGS_MODULE=mayan.settings.production \
    MAYAN_CELERY_BROKER_URL="amqp://$RABBITMQ_USER:$RABBITMQ_PASSWORD@$RABBITMQ_HOST:$RABBITMQ_PORT/$RABBITMQ_VHOST" \
    MAYAN_CELERY_RESULT_BACKEND="redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/1" \
    MAYAN_DATABASES="{'default':{'ENGINE':'django.db.backends.postgresql','HOST':'$DB_HOST','NAME':'$DB_NAME','PASSWORD':'$DB_PASSWORD','USER':'$DB_USER'}}" \
    MAYAN_LOCK_MANAGER_BACKEND="mayan.apps.lock_manager.backends.redis_lock.RedisLock" \
    MAYAN_LOCK_MANAGER_BACKEND_ARGUMENTS="{'redis_url':'redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/2'}" \
    MAYAN_MEDIA_ROOT="$MEDIA_DIR/" \
    "$VENV_DIR/bin/python" "$APP_DIR/bin/mayan-edms.py" common_initial_setup --force

chown -R "$APP_USER" "$MEDIA_DIR"

# ---- Supervisor ----
echo "[10/10] Démarrage de Supervisor..."
systemctl enable supervisor
systemctl restart supervisor

# ---- Nginx + SSL ----
if [[ "$NGINX_ENABLE" =~ ^[oO]$ ]]; then
    echo "Configuration de Nginx + SSL..."
    apt-get install --yes nginx certbot python3-certbot-nginx

    cat > "/etc/nginx/sites-available/egyptian" << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    client_max_body_size 512M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
NGINXEOF

    ln -sf /etc/nginx/sites-available/egyptian /etc/nginx/sites-enabled/
    nginx -t
    systemctl enable nginx
    systemctl reload nginx
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$CERTBOT_EMAIL"
fi

echo ""
echo "=========================================="
echo "  Installation terminée!"
if [[ "$NGINX_ENABLE" =~ ^[oO]$ ]]; then
    echo "  Application disponible sur : https://$DOMAIN_NAME"
else
    echo "  Application disponible sur : http://$ALLOWED_HOST:8000"
fi
echo "=========================================="
