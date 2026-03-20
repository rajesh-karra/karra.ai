#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/karra.ai"

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git

if [[ ! -d "$APP_DIR" ]]; then
    echo "Creating app directory at $APP_DIR"
    sudo mkdir -p "$APP_DIR"
    sudo chown -R "$USER":"$USER" "$APP_DIR"
fi

echo "Syncing project files..."
rsync -av --delete --exclude '.git' ./ "$APP_DIR"/

cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example. Edit it before starting the service."
fi

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_portfolio_data
python manage.py sync_github_profile --username r-karra
python manage.py sync_quantum_ai_knowledge

sudo cp deploy/systemd/karra.service /etc/systemd/system/karra.service
sudo cp deploy/systemd/karra-knowledge-sync.service /etc/systemd/system/karra-knowledge-sync.service
sudo cp deploy/systemd/karra-knowledge-sync.timer /etc/systemd/system/karra-knowledge-sync.timer
sudo cp deploy/nginx/karra.conf /etc/nginx/sites-available/karra
sudo ln -sf /etc/nginx/sites-available/karra /etc/nginx/sites-enabled/karra
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable karra
sudo systemctl enable karra-knowledge-sync.timer
sudo systemctl restart karra
sudo systemctl restart karra-knowledge-sync.timer
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment bootstrap complete."
