"""
Gunicorn Production Configuration for Blog SaaS Platform
"""
import multiprocessing

# Server Socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
capture_output = True

# Process Naming
proc_name = "blog_saas_gunicorn"

# Server Mechanics
daemon = False
pidfile = "/run/gunicorn/blog_saas.pid"
user = "www-data"
group = "www-data"
