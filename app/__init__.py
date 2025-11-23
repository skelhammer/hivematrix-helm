from flask import Flask
import json
import os
from dotenv import load_dotenv

# Load environment variables from .flaskenv
load_dotenv('.flaskenv')

app = Flask(__name__, instance_relative_config=True)

# Set secret key for session management (required for flash messages)
import secrets
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Session configuration for working behind proxy
app.config['SESSION_COOKIE_NAME'] = 'helm_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Disable static file caching in development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No caching for static files

# Configure logging level from environment
import logging
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
app.logger.setLevel(getattr(logging, log_level, logging.INFO))

# Enable structured JSON logging with correlation IDs
# Set ENABLE_JSON_LOGGING=false in environment to disable for development
enable_json = os.environ.get("ENABLE_JSON_LOGGING", "true").lower() in ("true", "1", "yes")
if enable_json:
    from app.structured_logger import setup_structured_logging
    setup_structured_logging(app, enable_json=True)

# --- Explicitly load all required configuration from environment variables ---
app.config['CORE_SERVICE_URL'] = os.environ.get('CORE_SERVICE_URL', 'http://localhost:5000')
app.config['SERVICE_NAME'] = os.environ.get('SERVICE_NAME', 'helm')

# Helm can run without Core - authentication will be disabled for UI but service management works
if not app.config['CORE_SERVICE_URL']:
    print("WARNING: CORE_SERVICE_URL not set. Authentication will be disabled.")
    print("Service management will still work, but admin dashboard authentication will not.")

# Load database connection from config file
import configparser
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

config_path = os.path.join(app.instance_path, 'helm.conf')
config = configparser.RawConfigParser()
config.read(config_path)
app.config['HELM_CONFIG'] = config

# Database configuration - PostgreSQL only
db_connection = config.get('database', 'connection_string', fallback=None)

if not db_connection:
    # If no database configured, use a dummy URI
    # init_db.py will configure it properly
    print("WARNING: Database not configured. Using temporary configuration.")
    print("Please complete the setup by running: python init_db.py")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/postgres'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_connection

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connection pool configuration for better performance
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,  # Recycle connections after 1 hour
    'pool_pre_ping': True,  # Test connections before use
    'max_overflow': 5,
}

# Load services configuration for service discovery and management
try:
    with open('services.json') as f:
        services_config = json.load(f)
        app.config['SERVICES'] = services_config
except FileNotFoundError:
    print("WARNING: services.json not found. Service management will not work.")
    app.config['SERVICES'] = {}

from extensions import db
db.init_app(app)

# Configure rate limiting
from flask_limiter import Limiter
from app.rate_limit_key import get_user_id_or_ip

limiter = Limiter(
    app=app,
    key_func=get_user_id_or_ip,  # Per-user rate limiting
    default_limits=["10000 per hour", "500 per minute"],
    storage_uri="memory://"
)

# Apply middleware to handle URL prefix when behind Nexus proxy
from app.middleware import PrefixMiddleware
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=f'/{app.config["SERVICE_NAME"]}')

# Register RFC 7807 error handlers for consistent API error responses
from app.error_responses import (
    internal_server_error,
    not_found,
    bad_request,
    unauthorized,
    forbidden,
    service_unavailable
)

@app.errorhandler(400)
def handle_bad_request(e):
    """Handle 400 Bad Request errors"""
    return bad_request(detail=str(e))

@app.errorhandler(401)
def handle_unauthorized(e):
    """Handle 401 Unauthorized errors"""
    return unauthorized(detail=str(e))

@app.errorhandler(403)
def handle_forbidden(e):
    """Handle 403 Forbidden errors"""
    return forbidden(detail=str(e))

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 Not Found errors"""
    return not_found(detail=str(e))

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 Internal Server Error"""
    app.logger.error(f"Internal server error: {e}")
    return internal_server_error()

@app.errorhandler(503)
def handle_service_unavailable(e):
    """Handle 503 Service Unavailable errors"""
    return service_unavailable(detail=str(e))

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Catch-all handler for unexpected exceptions"""
    app.logger.exception(f"Unexpected error: {e}")
    return internal_server_error(detail="An unexpected error occurred")

# Import routes
from app import routes
from app import api_routes

# Start log file watcher in background thread
import threading
from pathlib import Path

def start_log_watcher_thread():
    """Start the log watcher in a background thread"""
    from log_watcher import start_log_watcher
    watcher_thread = threading.Thread(target=start_log_watcher, daemon=True)
    watcher_thread.start()

# Only start log watcher if logs directory exists (i.e., not during initial setup)
logs_dir = Path('logs')
if logs_dir.exists():
    start_log_watcher_thread()

# Add custom Jinja2 filters
from datetime import datetime, timezone

from app.version import VERSION, SERVICE_NAME as VERSION_SERVICE_NAME

# Context processor to inject version into all templates
@app.context_processor
def inject_version():
    return {
        'app_version': VERSION,
        'app_service_name': VERSION_SERVICE_NAME
    }

@app.template_filter('format_datetime')
def format_datetime(timestamp_str):
    """Convert ISO timestamp to human-readable format"""
    if not timestamp_str:
        return '-'

    try:
        # Parse ISO format timestamp
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str

        # Format nicely: "Nov 19, 2025 10:09 PM"
        return dt.strftime('%b %d, %Y %I:%M %p')
    except Exception as e:
        return str(timestamp_str)

@app.template_filter('format_uptime')
def format_uptime(timestamp_str):
    """Convert ISO timestamp to human-readable uptime"""
    if not timestamp_str:
        return '-'

    try:
        # Parse ISO format timestamp
        if isinstance(timestamp_str, str):
            started_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            started_at = timestamp_str

        # Calculate uptime using local time for comparison
        # Database stores UTC, so we compare with UTC now
        if started_at.tzinfo is None:
            # Naive datetime from database - assume it's UTC
            started_at = started_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = now - started_at

        # Format based on duration
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return '-'
        elif total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours > 0:
                return f"{days}d {hours}h"
            return f"{days}d"
    except Exception as e:
        return '-'
