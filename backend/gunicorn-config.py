# Gunicorn configuration file
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5

# Add WebSocket support
wsgi_app = "main:app"
worker_connections = 1000