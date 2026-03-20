#!/bin/bash
# Quick venv-only rebuild for emergency fixes
# Use this when you only need to rebuild the Python environment

APP_DIR="/opt/karra.ai"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_USER="www-data"

echo "Quick Venv Rebuild"
echo "=================="

sudo systemctl stop karra || true
sudo rm -rf ${VENV_DIR}
cd ${APP_DIR}
sudo -u ${SERVICE_USER} python3 -m venv ${VENV_DIR}
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/pip install --upgrade pip
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/pip install -r requirements.txt

echo "✓ Venv rebuilt as www-data"
echo "Now run: sudo systemctl start karra"
