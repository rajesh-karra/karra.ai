#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/karra.ai"

cd "$APP_DIR"
source .venv/bin/activate

python manage.py sync_quantum_ai_knowledge
python manage.py collectstatic --noinput

deactivate
