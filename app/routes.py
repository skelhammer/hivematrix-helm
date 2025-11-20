"""
Web UI routes for Helm dashboard
"""

from flask import render_template, g, request, redirect, url_for, flash, jsonify
from app import app
from app.auth import token_required, admin_required
from app.service_manager import ServiceManager
from models import LogEntry, ServiceStatus
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

@app.route('/')
@token_required
def index():
    """Main dashboard showing all services"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    # Get all service statuses
    statuses = ServiceManager.get_all_service_statuses()

    # Get recent log statistics for all services in one query
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    
    counts = (
        LogEntry.query
        .filter(LogEntry.timestamp >= one_hour_ago)
        .with_entities(LogEntry.service_name, LogEntry.level, func.count(LogEntry.id))
        .group_by(LogEntry.service_name, LogEntry.level)
        .all()
    )

    # Process the results into the desired format
    log_stats = {}
    for service_name, level, count in counts:
        if service_name not in log_stats:
            log_stats[service_name] = {}
        log_stats[service_name][level] = count

    # Ensure all services have a log_stats entry, even if empty
    for service_name in statuses.keys():
        if service_name not in log_stats:
            log_stats[service_name] = {}

    return render_template(
        'index.html',
        user=g.user,
        statuses=statuses,
        log_stats=log_stats
    )


@app.route('/service/<service_name>')
@token_required
def service_detail(service_name):
    """Detailed view of a specific service"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    try:
        status = ServiceManager.get_service_status(service_name)
    except ValueError:
        return "Service not found", 404

    # Get recent logs for this service
    recent_logs = (
        LogEntry.query
        .filter_by(service_name=service_name)
        .order_by(LogEntry.timestamp.desc())
        .limit(50)
        .all()
    )

    return render_template(
        'service_detail.html',
        user=g.user,
        service_name=service_name,
        status=status,
        logs=recent_logs
    )


@app.route('/logs')
@token_required
def logs_view():
    """Log viewer with filtering"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    # Get filter parameters
    service = request.args.get('service')
    level = request.args.get('level')
    limit = min(int(request.args.get('limit', 100)), 500)

    # Build query
    query = LogEntry.query

    if service:
        query = query.filter_by(service_name=service)

    if level:
        query = query.filter_by(level=level.upper())

    # Get logs
    logs = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()

    # Get available services for filter
    services = ServiceManager.get_all_services()

    return render_template(
        'logs.html',
        user=g.user,
        logs=logs,
        services=services,
        selected_service=service,
        selected_level=level
    )


@app.route('/metrics')
@token_required
def metrics_view():
    """Metrics and performance monitoring"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    statuses = ServiceManager.get_all_service_statuses()

    # Calculate actual uptime for running services
    for service_name, status in statuses.items():
        if status.get('status') == 'running' and status.get('started_at'):
            # Calculate uptime for running services
            started_at = status['started_at']
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))

            now = datetime.now(timezone.utc)
            delta = now - started_at.replace(tzinfo=None)
            total_seconds = int(delta.total_seconds())

            # Format uptime
            if total_seconds < 60:
                uptime = f"{total_seconds}s"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                uptime = f"{minutes}m"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                uptime = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            else:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                uptime = f"{days}d {hours}h" if hours > 0 else f"{days}d"

            status['uptime'] = uptime
        else:
            status['uptime'] = '-'

    # Get recent log statistics
    log_stats = {}
    for service_name in statuses.keys():
        # Count logs by level in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        counts = (
            LogEntry.query
            .filter(LogEntry.service_name == service_name)
            .filter(LogEntry.timestamp >= one_hour_ago)
            .with_entities(LogEntry.level, func.count(LogEntry.id))
            .group_by(LogEntry.level)
            .all()
        )

        log_stats[service_name] = {level: count for level, count in counts}

    return render_template(
        'metrics.html',
        user=g.user,
        statuses=statuses,
        log_stats=log_stats
    )


@app.route('/service/<service_name>/logs')
@token_required
def service_logs(service_name):
    """View stdout/stderr logs for a service"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    # Get query parameters
    lines = min(int(request.args.get('lines', 100)), 1000)
    log_type = request.args.get('type', 'both')  # stdout, stderr, or both

    try:
        logs = ServiceManager.get_service_logs(service_name, lines=lines, log_type=log_type)
        status = ServiceManager.get_service_status(service_name)
    except ValueError:
        return "Service not found", 404

    return render_template(
        'service_logs.html',
        user=g.user,
        service_name=service_name,
        status=status,
        logs=logs,
        log_type=log_type,
        lines=lines
    )


@app.route('/users')
@admin_required
def users_management():
    """User and group management page for Keycloak"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    return render_template(
        'users.html',
        user=g.user
    )


@app.route('/security')
@token_required
def security_dashboard():
    """Security audit and firewall configuration dashboard"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    return render_template(
        'security.html',
        user=g.user
    )
