#!/usr/bin/env bash
set -euo pipefail

# One-command production deploy for GCP E2 + Neon PostgreSQL.
# Usage:
#   ./scripts/deploy_gcp_e2_neon.sh \
#     --database-url "postgresql://..." \
#     --allowed-hosts "example.com,VM_IP" \
#     --secret-key "your-secret"

APP_DIR="/opt/karra.ai"
APP_USER="www-data"
DATABASE_URL=""
ALLOWED_HOSTS=""
SECRET_KEY=""
SECURE_SSL_REDIRECT="True"
DOMAIN=""
EMAIL=""
DRY_RUN="false"

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[dry-run] $*"
    return 0
  fi
  "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --database-url)
      DATABASE_URL="$2"
      shift 2
      ;;
    --allowed-hosts)
      ALLOWED_HOSTS="$2"
      shift 2
      ;;
    --secret-key)
      SECRET_KEY="$2"
      shift 2
      ;;
    --secure-ssl-redirect)
      SECURE_SSL_REDIRECT="$2"
      shift 2
      ;;
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$DATABASE_URL" || -z "$ALLOWED_HOSTS" || -z "$SECRET_KEY" ]]; then
  echo "Missing required args."
  echo "Required: --database-url --allowed-hosts --secret-key"
  exit 1
fi

echo "[1/8] Installing system packages..."
run_cmd sudo apt update
run_cmd sudo apt install -y python3 python3-venv python3-pip nginx git rsync

if [[ ! -d "$APP_DIR" ]]; then
  echo "Creating app directory at $APP_DIR"
  run_cmd sudo mkdir -p "$APP_DIR"
fi
run_cmd sudo chown -R "$USER":"$USER" "$APP_DIR"

echo "[2/8] Syncing project files to $APP_DIR..."
run_cmd rsync -av --delete --exclude '.git' ./ "$APP_DIR"/

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] cd $APP_DIR"
else
  cd "$APP_DIR"
fi

echo "[3/8] Creating virtual environment and installing dependencies..."
run_cmd python3 -m venv .venv

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] source .venv/bin/activate"
  echo "[dry-run] pip install --upgrade pip"
  echo "[dry-run] pip install -r requirements.txt"
else
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

echo "[4/8] Writing production .env..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] write $APP_DIR/.env with DJANGO_* and DATABASE_URL"
else
cat > .env <<EOF
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$ALLOWED_HOSTS
DJANGO_SECURE_SSL_REDIRECT=$SECURE_SSL_REDIRECT
DATABASE_URL=$DATABASE_URL
EOF
fi

# Validate DB connectivity before migrations.
echo "[5/8] Validating Neon DB connectivity..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] validate Neon DB connectivity with SELECT 1"
else
"$APP_DIR/.venv/bin/python" - <<'PY'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
print('Neon DB connection: OK')
PY
fi

echo "[6/8] Running migrations, static collection, and seed sync..."
run_cmd python manage.py migrate
run_cmd python manage.py collectstatic --noinput
run_cmd python manage.py sync_github_profile --username r-karra
run_cmd python manage.py import_topic_scenarios_json --file data/topic_scenarios.json --replace
run_cmd python manage.py check

echo "[7/8] Configuring systemd and nginx..."
run_cmd sudo cp deploy/systemd/karra.service /etc/systemd/system/karra.service
run_cmd sudo cp deploy/nginx/karra.conf /etc/nginx/sites-available/karra

if [[ -n "$DOMAIN" ]]; then
  run_cmd sudo sed -i "s/server_name _;/server_name $DOMAIN;/" /etc/nginx/sites-available/karra
fi

run_cmd sudo ln -sf /etc/nginx/sites-available/karra /etc/nginx/sites-enabled/karra
run_cmd sudo rm -f /etc/nginx/sites-enabled/default

run_cmd sudo chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
run_cmd sudo systemctl daemon-reload
run_cmd sudo systemctl enable karra
run_cmd sudo systemctl restart karra
run_cmd sudo nginx -t
run_cmd sudo systemctl restart nginx

if [[ -n "$DOMAIN" ]]; then
  if [[ -z "$EMAIL" ]]; then
    echo "--email is required when --domain is provided."
    exit 1
  fi

  echo "[8/9] Installing certbot and issuing TLS certificate..."
  run_cmd sudo apt install -y certbot python3-certbot-nginx
  run_cmd sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect
  run_cmd sudo systemctl reload nginx
  echo "TLS certificate configured for $DOMAIN"

  echo "[9/9] Deployment complete with HTTPS."
else
  echo "[8/8] Deployment complete."
fi

echo "Run: sudo systemctl status karra && sudo systemctl status nginx"
