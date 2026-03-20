# Production Performance Fixes & Deployment Guide

## Summary of Changes

This document outlines the performance optimizations made to address the slowness issue on production (`https://104-198-18-62.sslip.io/`).

### Performance Optimizations Implemented

#### 1. **Knowledge Graph Caching** (Major - saves ~5 DB queries per page)
   - File: `portfolio/views.py`
   - Change: Added 5-minute in-memory cache to `HomeView._build_knowledge_graph_from_db()`
   - Impact: Reduces database queries for knowledge graph on every home page load
   - Cache: Django local memory cache, 10,000 max entries

#### 2. **Regex Pattern Pre-compilation** (Moderate - saves regex compilation overhead)
   - File: `portfolio/views.py`
   - Changes:
     - Pre-compile URL matching patterns at module load (not on every request)
     - Cache keyword highlighting patterns after first use
   - Impact: Reduces CPU usage on text rendering

#### 3. **Gunicorn Worker Scaling** (Major - adapts to VM size)
   - File: `gunicorn_conf.py`
   - Changes:
     - Workers now dynamically scale: `(2 * CPU_cores) + 1`
     - Added `max_requests` (1000) to prevent memory leaks
     - Added `keepalive` (5s) for persistent connections
     - Override with `GUNICORN_WORKERS` env var if needed
   - Impact: Better concurrency, automatic CPU adaptation

#### 4. **Django Cache Backend** (Foundation for optimizations)
   - File: `config/settings.py`
   - Added: Local memory cache backend (LocMemCache)
   - Capacity: 10,000 entries, auto-eviction when full

---

## Deployment Instructions

### Option A: Full Automated Deployment (Recommended)

If you have sudo access on the production VM:

```bash
# On your local machine
scp scripts/deploy_fix_performance.sh ubuntu@104-198-18-62.sslip.io:/tmp/

# SSH into the VM
ssh ubuntu@104-198-18-62.sslip.io

# Run the deployment script
bash /tmp/deploy_fix_performance.sh
```

This script will:
1. Fix directory ownership
2. Stop the service
3. Rebuild Python venv as `www-data`
4. Install dependencies
5. Run migrations
6. Collect static files
7. Restart the service
8. Verify deployment

### Option B: Manual Step-by-Step Deployment

If automated script doesn't work, run these commands:

```bash
# SSH into the VM
ssh ubuntu@104-198-18-62.sslip.io

# 1. Fix ownership
sudo chown -R www-data:www-data /opt/karra.ai
sudo chmod -R u+w /opt/karra.ai

# 2. Stop service
sudo systemctl stop karra
sudo systemctl reset-failed karra

# 3. Remove old venv and rebuild
cd /opt/karra.ai
sudo rm -rf .venv
sudo -u www-data python3 -m venv .venv

# 4. Install dependencies
sudo -u www-data .venv/bin/pip install --upgrade pip
sudo -u www-data .venv/bin/pip install -r requirements.txt

# 5. Apply migrations and collect statics
sudo -u www-data .venv/bin/python manage.py migrate --noinput
sudo -u www-data .venv/bin/python manage.py collectstatic --noinput

# 6. Start service
sudo systemctl daemon-reload
sudo systemctl start karra

# 7. Verify
sleep 2
sudo systemctl status karra
curl http://127.0.0.1:8000/
```

### Option C: Quick Venv Rebuild (Emergency Fix)

If you only need to rebuild the venv:

```bash
bash scripts/quick_venv_fix.sh
```

---

## Verification Steps

After deployment, run these checks:

### Local Endpoint Test
```bash
curl -I http://127.0.0.1:8000/
# Should return: HTTP/1.1 200 OK
```

### Service Status
```bash
sudo systemctl status karra
# Should show: Active: active (running)
```

### View Recent Logs
```bash
sudo journalctl -u karra -n 50 --no-pager
```

### Monitor Server Load
```bash
# Check CPU and memory during high traffic
top -p $(pgrep -f gunicorn | tr '\n' ',')
```

### Test Admin Login (should be fast now)
```bash
curl -X POST \
  -d "username=admin&password=Admin12345" \
  https://104-198-18-62.sslip.io/admin/login/
```

---

## Performance Tuning

### Adjust GunicornWorkers
If you want to manually set worker count, set env var:
```bash
export GUNICORN_WORKERS=8  # Pick based on CPU cores
systemctl restart karra
```

### Adjust Cache Timeout
If knowledge graph updates frequently, reduce cache timeout in `portfolio/views.py`:
```python
# Current: 300 seconds (5 minutes)
# Change to: 60 (1 minute) or any other value
cache.set(cache_key, result, 60)  # <-- duration in seconds
```

### Monitor Cache Hit Rate
```python
# In Django shell or management command
from django.core.cache import cache
print(cache.get('knowledge_graph_home_view'))  # Should be not None on repeat loads
```

---

## Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Home page queries | ~8-10 DB queries | ~0-2 DB queries (cached) | **5-10x faster** |
| Regex compilation | Per request | Once at startup | **Significant CPU savings** |  
| Concurrent requests | 3 workers (bottleneck) | Auto-scaled (4-16+) | **Better concurrency** |
| Memory per worker | Unbounded | 1000 req limit | **Prevents memory leaks** |

---

## Troubleshooting

### Service keeps crashing with `Failed to find gunicorn`
- The venv wasn't created properly
- Run: `ls -la /opt/karra.ai/.venv/bin/gunicorn`
- If missing, rebuild venv as www-data: `sudo -u www-data python3 -m venv /opt/karra.ai/.venv`

### Still getting `502 Bad Gateway`
1. Check service status: `sudo systemctl status karra`
2. View errors: `sudo journalctl -u karra -n 100 --no-pager | grep -i error`
3. Test local endpoint: `curl -v http://127.0.0.1:8000/`
4. If local fails, diagnose Django: `cd /opt/karra.ai && .venv/bin/python manage.py check`

### Cache not working
- Verify in Django shell: `from django.core.cache import cache; cache.set('test', 'value'); print(cache.get('test'))`
- If None, check if LocMemCache backend is active in `config/settings.py`

### Still slow after deployment
1. Check Django settings: `curl http://127.0.0.1:8000/admin/ -I` (verify `DJANGO_DEBUG=False` in logs)
2. Profile queries: Add `django-debug-toolbar` for local profiling
3. Check database response: `time psql $DATABASE_URL -c "SELECT 1;"`
4. Monitor worker count: `ps aux | grep gunicorn | grep -v grep | wc -l`

---

## Rollback

If issues occur after deployment:

```bash
# Option 1: Restart and let systemd restart automatically
sudo systemctl restart karra

# Option 2: Revert code changes and redeploy
git -C /opt/karra.ai checkout config/settings.py portfolio/views.py gunicorn_conf.py
sudo systemctl restart karra

# Option 3: Rebuild venv with previous requirements
sudo -u www-data /opt/karra.ai/.venv/bin/pip install -r /opt/karra.ai/requirements.txt
```

---

## Generated Files

- `scripts/deploy_fix_performance.sh` - Full automated deployment
- `scripts/quick_venv_fix.sh` - Quick venv rebuild only
- `config/settings.py` - Updated with cache backend
- `portfolio/views.py` - Optimized with caching and regex pre-compilation
- `gunicorn_conf.py` - Updated with worker scaling

---

## Next Steps

1. **Deploy** using one of the options above
2. **Verify** using the verification steps
3. **Monitor** with `sudo journalctl -u karra -f` during traffic
4. **Measure** performance improvement and collect metrics
5. **Adjust** cache timeouts and worker count as needed based on actual performance

