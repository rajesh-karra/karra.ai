import os
import multiprocessing

bind = "127.0.0.1:8000"

# Worker count: (2 * CPU cores) + 1 for async workers
# Override with GUNICORN_WORKERS env var if needed
def get_worker_count():
    env_workers = os.getenv("GUNICORN_WORKERS")
    if env_workers:
        return int(env_workers)
    # Default: (2 * cores) + 1, minimum 4
    cpu_count = multiprocessing.cpu_count()
    return max(4, (2 * cpu_count) + 1)

workers = get_worker_count()
timeout = 120
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"

# Increase max requests per worker to reduce memory buildup
max_requests = 1000
max_requests_jitter = 100

# Keep-alive for persistent connections
keepalive = 5

