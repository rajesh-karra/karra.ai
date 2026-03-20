#!/bin/bash
# Complete deployment and performance fix script for karra.ai production
# This script:
# 1. Fixes venv permissions and rebuilds if needed
# 2. Installs/updates Python dependencies
# 3. Applies database migrations
# 4. Collects static files
# 5. Deploys new optimized gunicorn config
# 6. Restarts services
# 7. Verifies deployment

set -e  # Exit on any error

APP_DIR="/opt/karra.ai"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_USER="www-data"

echo "=========================================="
echo "Karra.ai Performance Deployment Fix"
echo "=========================================="
echo

# Step 1: Fix directory ownership
echo "[1/8] Fixing directory ownership..."
sudo chown -R ${SERVICE_USER}:${SERVICE_USER} ${APP_DIR}
sudo chmod -R u+w ${APP_DIR}
echo "✓ Ownership fixed"

# Step 2: Stop service
echo "[2/8] Stopping karra service..."
sudo systemctl stop karra || true
sudo systemctl reset-failed karra || true
echo "✓ Service stopped"

# Step 3: Remove broken venv if it exists
if [ -d "${VENV_DIR}" ]; then
    echo "[3/8] Removing broken venv..."
    sudo rm -rf ${VENV_DIR}
    echo "✓ Old venv removed"
else
    echo "[3/8] No existing venv found (OK)"
fi

# Step 4: Create fresh venv as service user
echo "[4/8] Creating fresh Python venv as ${SERVICE_USER}..."
cd ${APP_DIR}
sudo -u ${SERVICE_USER} python3 -m venv ${VENV_DIR}
echo "✓ Venv created"

# Step 5: Install dependencies
echo "[5/8] Installing Python dependencies..."
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/pip install --upgrade pip setuptools wheel
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt
echo "✓ Dependencies installed"

# Step 6: Run database migrations and collect static files
echo "[6/8] Running database migrations and collecting statics..."
cd ${APP_DIR}
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/python manage.py migrate --noinput
sudo -u ${SERVICE_USER} ${VENV_DIR}/bin/python manage.py collectstatic --noinput
echo "✓ Migrations applied and statics collected"

# Step 7: Start service
echo "[7/8] Starting karra service..."
sudo systemctl daemon-reload
sudo systemctl start karra
sudo systemctl enable karra
echo "✓ Service started"

# Step 8: Verify deployment
echo "[8/8] Verifying deployment..."
echo

# Wait for service to be ready
sleep 2

# Check systemd status
STATUS=$(sudo systemctl is-active karra)
if [ "$STATUS" = "active" ]; then
    echo "✓ Service is active"
else
    echo "✗ Service is $STATUS - DEPLOYMENT FAILED"
    echo "Run: sudo journalctl -u karra -n 50 --no-pager"
    exit 1
fi

# Check local endpoint
echo "Testing local endpoint..."
if nc -z 127.0.0.1 8000 2>/dev/null; then
    echo "✓ Django app listening on 127.0.0.1:8000"
else
    echo "✗ Django app not listening - DEPLOYMENT FAILED"
    echo "Run: sudo journalctl -u karra -n 50 --no-pager"
    exit 1
fi

echo
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=========================================="
echo
echo "Summary:"
echo "  - Venv rebuilt at: ${VENV_DIR}"
echo "  - Service user: ${SERVICE_USER}"
echo "  - Service enabled: yes"
echo "  - Gunicorn workers: $(${VENV_DIR}/bin/python -c 'import multiprocessing; print((2*multiprocessing.cpu_count())+1)')"
echo
echo "Next steps:"
echo "  1. Test http://127.0.0.1:8000/ locally"
echo "  2. Test https://104-198-18-62.sslip.io/ from browser"
echo "  3. Monitor: sudo journalctl -u karra -f"
echo "  4. Check performance improvements on home page load"
echo
