# karra.ai

Personal website built with Django + FastAPI on a shared ASGI stack, using Neon PostgreSQL.

## Features

- Professional clean white UI
- Menu structure: About Me - Quantum ∞ AI
- Live animated entanglement symbol between Quantum and AI
- Quantum and AI tabs segregated into:
	- Source
	- Resources
	- Video Lectures
	- Blog
- Entanglement logic:
	- Items flagged as entangled appear in both Quantum and AI views
- GitHub profile sync for `https://github.com/r-karra`
- Shared PostgreSQL connection via Neon
- FastAPI endpoints mounted at `/api/*`
- Deployment assets for GCP E2 instance (systemd + nginx)

## Tech Stack

- Django 5
- FastAPI
- PostgreSQL (Neon)
- Gunicorn + Uvicorn worker
- WhiteNoise static serving

## Project Structure

```
config/                 # Django project config + ASGI composition
portfolio/              # Models, views, admin, management commands
api/                    # FastAPI app
templates/              # Django templates
static/                 # CSS and JS
deploy/systemd/         # systemd service file
deploy/nginx/           # nginx reverse proxy config
scripts/                # GCP bootstrap script
```

## Environment Variables

Create `.env` from `.env.example` and set values:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DATABASE_URL`

Neon format:

`postgresql://user:password@host/dbname?sslmode=require&channel_binding=require`

## Connect Neon Database

1. Create a Neon project and copy the connection string from Neon dashboard.
2. Put it into `.env` as `DATABASE_URL`.
3. Verify DB connectivity:

```bash
python manage.py migrate
python manage.py check
```

4. Optional: seed data for profile and scenarios:

```bash
python manage.py sync_github_profile --username r-karra
python manage.py import_topic_scenarios_json --file data/topic_scenarios.json --replace
```

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Neon credentials and allowed hosts.

Then run:

```bash
python manage.py migrate
python manage.py seed_portfolio_data
python manage.py sync_github_profile --username r-karra
python manage.py runserver
```

Open: `http://127.0.0.1:8000`

## API Endpoints

- `GET /api/health`
- `GET /api/profile`
- `GET /api/resources`
- `GET /api/resources?domain=quantum`
- `GET /api/resources?domain=ai`

## Scenario Content (Neon DB, No Admin)

Quantum/AI scenario content can be edited in a JSON file and imported directly
to Neon PostgreSQL without using Django admin.

1. Edit [data/topic_scenarios.json](data/topic_scenarios.json)
2. Import into DB:

```bash
python manage.py import_topic_scenarios_json --file data/topic_scenarios.json --replace
```

This updates the `TopicScenario` table that powers the Quantum and AI tabs.

## Deploy to GCP E2

### 1) Create VM

- Create an E2 VM (Ubuntu) in GCP Compute Engine.
- Open firewall ports: `80` and `443`.
- SSH into VM.

### 2) Copy Project and Configure Env

- Copy/clone this repository to VM.
- Create `/opt/karra.ai/.env` with:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_DEBUG=False`
	- `DJANGO_ALLOWED_HOSTS=<your-domain-or-vm-ip>`
	- `DJANGO_SECURE_SSL_REDIRECT=True`
	- `DATABASE_URL=<your-neon-connection-string>`

### 3) Install and Start Services

Recommended one-command deploy (Neon + GCP E2):

```bash
chmod +x scripts/deploy_gcp_e2_neon.sh
./scripts/deploy_gcp_e2_neon.sh \
	--database-url "postgresql://user:password@host/dbname?sslmode=require&channel_binding=require" \
	--allowed-hosts "your-domain.com,VM_PUBLIC_IP" \
	--secret-key "replace-with-strong-secret"
```

Optional HTTPS automation in the same command:

```bash
./scripts/deploy_gcp_e2_neon.sh \
	--database-url "postgresql://user:password@host/dbname?sslmode=require&channel_binding=require" \
	--allowed-hosts "your-domain.com,VM_PUBLIC_IP" \
	--secret-key "replace-with-strong-secret" \
	--domain "your-domain.com" \
	--email "you@example.com"
```

Preview everything without making changes:

```bash
./scripts/deploy_gcp_e2_neon.sh \
	--database-url "postgresql://user:password@host/dbname?sslmode=require&channel_binding=require" \
	--allowed-hosts "your-domain.com,VM_PUBLIC_IP" \
	--secret-key "replace-with-strong-secret" \
	--domain "your-domain.com" \
	--email "you@example.com" \
	--dry-run
```

This command installs dependencies, writes production `.env`, validates Neon connectivity,
runs migrations, imports scenarios, and starts systemd/nginx.

Alternative manual bootstrap:

On your VM, clone/copy this project and run:

```bash
chmod +x scripts/bootstrap_gcp_e2.sh
./scripts/bootstrap_gcp_e2.sh
```

This script will:

- Install Python and nginx
- Set up virtualenv and dependencies
- Run migrations and collectstatic
- Seed portfolio content
- Sync GitHub profile data
- Configure systemd service and nginx

### 4) Post-Deploy Checks

```bash
sudo systemctl status karra
sudo systemctl status nginx
curl -I http://127.0.0.1:8000
```

### 5) Enable HTTPS (Recommended)

- Point your domain DNS `A` record to VM public IP.
- Install certbot and issue TLS cert for nginx.
- Keep `DJANGO_SECURE_SSL_REDIRECT=True` in production.

After first run, update `/opt/karra.ai/.env` with production values and restart services:

```bash
sudo systemctl restart karra
sudo systemctl restart nginx
```

### 6) Pull Latest GitHub Changes to GCP VM

SSH to VM and run:

```bash
cd /opt/karra.ai
git status
git fetch origin
git pull --rebase origin main
```

If the VM is deploy-only and you want it to match GitHub exactly:

```bash
cd /opt/karra.ai
git fetch origin
git reset --hard origin/main
```

Reinstall/update Python dependencies and restart services:

```bash
cd /opt/karra.ai
source .venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart karra
sudo systemctl restart nginx
```

Exact end-to-end update commands (copy/paste on VM):

```bash
cd /opt/karra.ai

# 1) Check repo state
git status
git remote -v
git branch --show-current

# 2) If there are local edits, stash them first (safe)
git stash push -u -m "temp-before-pull-$(date +%F-%H%M%S)"

# 3) Pull latest code from GitHub main
git fetch origin
git reset --hard origin/main

# 4) Update Python deps and run Django tasks
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
deactivate

# 5) Restart app services
sudo systemctl restart karra
sudo systemctl restart nginx

# 6) Verify
sudo systemctl status karra --no-pager -l
sudo systemctl status nginx --no-pager -l
curl -I https://104-198-18-62.sslip.io
```

### 7) Apply Neon DB Updates After Pull

After code updates, run migrations and sync content:

```bash
cd /opt/karra.ai
source .venv/bin/activate
python manage.py migrate
python manage.py import_topic_scenarios_json --file data/topic_scenarios.json --replace
python manage.py sync_github_profile --username r-karra
python manage.py check
deactivate
sudo systemctl restart karra
```

If your `DATABASE_URL` changed, update `/opt/karra.ai/.env` first and then run the same commands.

### 8) Custom Domain + HTTPS Setup (VM + nginx)

1. Point DNS `A` records to your VM public IP.
2. Update nginx hostnames and Django allowed hosts.
3. Issue and deploy TLS certificate with certbot.

Example commands:

```bash
# Replace these values
DOMAIN="example.com"
WWW_DOMAIN="www.example.com"
EMAIL="you@your-email.com"
APP_ENV="/opt/karra.ai/.env"

# nginx server_name
sudo sed -Ei "s|^\s*server_name\s+[^;]+;|    server_name ${DOMAIN} ${WWW_DOMAIN};|" /etc/nginx/sites-available/karra

# Django allowed hosts
if sudo grep -q '^DJANGO_ALLOWED_HOSTS=' "$APP_ENV"; then
	sudo sed -i "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=${DOMAIN},${WWW_DOMAIN},127.0.0.1,localhost|" "$APP_ENV"
else
	echo "DJANGO_ALLOWED_HOSTS=${DOMAIN},${WWW_DOMAIN},127.0.0.1,localhost" | sudo tee -a "$APP_ENV" >/dev/null
fi

# Force HTTPS redirects in Django
if sudo grep -q '^DJANGO_SECURE_SSL_REDIRECT=' "$APP_ENV"; then
	sudo sed -i 's|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=True|' "$APP_ENV"
else
	echo 'DJANGO_SECURE_SSL_REDIRECT=True' | sudo tee -a "$APP_ENV" >/dev/null
fi

sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart karra

# Issue TLS cert and configure nginx redirect
sudo certbot --nginx -d "$DOMAIN" -d "$WWW_DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect

# Verify
sudo certbot certificates
curl -I "https://${DOMAIN}"
curl -I "https://${WWW_DOMAIN}"
```

Note: Certbot requires a real domain. It will not issue normal certificates for raw public IP addresses.

## Admin

Create admin user:

```bash
python manage.py createsuperuser
```

Admin panel is available at `/admin/`.