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
import json
import os

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
            # Ensure started_at is timezone-aware for comparison
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            delta = now - started_at
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


@app.route('/service/<service_name>/restart', methods=['POST'])
@admin_required
def restart_service_web(service_name):
    """Restart a specific service (web UI)"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    # Don't allow restarting Helm itself
    if service_name == 'helm':
        flash('Cannot restart Helm from the web interface. Use the CLI instead.', 'warning')
        return redirect(url_for('service_detail', service_name=service_name))

    try:
        result = ServiceManager.restart_service(service_name, 'development')
        if result.get('success'):
            flash(f'Successfully restarted {service_name}', 'success')
        else:
            error_msg = result.get('error', result.get('message', 'Unknown error'))
            flash(f'Failed to restart {service_name}: {error_msg}', 'error')
    except ValueError:
        flash(f'Service {service_name} not found', 'error')
    except Exception as e:
        app.logger.error(f'Error restarting {service_name}: {str(e)}')
        flash('Internal server error', 'error')

    return redirect(url_for('service_detail', service_name=service_name))


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


@app.route('/settings')
@admin_required
def settings():
    """System settings page"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    # Load master config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'configs', 'master_config.json')
    config = {}
    try:
        with open(config_path) as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        flash('Could not load master configuration', 'error')

    return render_template(
        'settings.html',
        user=g.user,
        config=config
    )


@app.route('/settings/save', methods=['POST'])
@admin_required
def save_settings():
    """Save system settings"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'configs', 'master_config.json')

    try:
        # Load existing config
        with open(config_path) as f:
            config = json.load(f)

        # Update settings from form
        if 'environment' in request.form:
            config['system']['environment'] = request.form['environment']
        if 'hostname' in request.form:
            config['system']['hostname'] = request.form['hostname']
        if 'log_level' in request.form:
            config['system']['log_level'] = request.form['log_level']

        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        # Auto-sync configuration to all services
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from config_manager import ConfigManager

            helm_dir = os.path.dirname(os.path.dirname(__file__))
            config_mgr = ConfigManager(helm_dir)
            config_mgr.sync_all_apps()

            flash('Settings saved and synced to all services. Restart services for changes to take effect.', 'success')
        except Exception as sync_error:
            app.logger.error(f'Settings saved, but sync failed: {str(sync_error)}')
            flash('Settings saved, but sync failed. Use Sync Configuration button.', 'warning')
    except Exception as e:
        app.logger.error(f'Error saving settings: {str(e)}')
        flash('Internal server error', 'error')

    return redirect(url_for('settings'))


@app.route('/settings/sync-config', methods=['POST'])
@admin_required
def sync_config():
    """Sync configuration to all services"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from config_manager import ConfigManager

        helm_dir = os.path.dirname(os.path.dirname(__file__))
        config_mgr = ConfigManager(helm_dir)
        config_mgr.sync_all_apps()

        flash('Configuration synced to all services successfully.', 'success')
    except Exception as e:
        app.logger.error(f'Error syncing configuration: {str(e)}')
        flash('Internal server error', 'error')

    return redirect(url_for('settings'))


@app.route('/settings/restart-all', methods=['POST'])
@admin_required
def restart_all_services():
    """Restart all running services"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    try:
        statuses = ServiceManager.get_all_service_statuses()
        restarted = []
        failed = []

        for service_name, status in statuses.items():
            if status.get('status') == 'running' and service_name != 'helm':
                result = ServiceManager.restart_service(service_name)
                if result.get('success'):
                    restarted.append(service_name)
                else:
                    failed.append(service_name)

        if restarted:
            flash(f'Restarted services: {", ".join(restarted)}', 'success')
        if failed:
            flash(f'Failed to restart: {", ".join(failed)}', 'error')
        if not restarted and not failed:
            flash('No services to restart.', 'info')

    except Exception as e:
        app.logger.error(f'Error restarting services: {str(e)}')
        flash('Internal server error', 'error')

    return redirect(url_for('settings'))


@app.route('/settings/ssl-info')
@admin_required
def ssl_info():
    """Get SSL certificate information"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    import subprocess
    from datetime import datetime

    cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'hivematrix-nexus', 'certs', 'nexus.crt')
    cert_info = {'exists': False}

    if os.path.exists(cert_path):
        cert_info['exists'] = True
        cert_info['path'] = cert_path

        try:
            # Get certificate details using openssl
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-noout', '-subject', '-enddate', '-issuer'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('subject='):
                        cert_info['subject'] = line.replace('subject=', '').strip()
                    elif line.startswith('notAfter='):
                        cert_info['expires'] = line.replace('notAfter=', '').strip()
                    elif line.startswith('issuer='):
                        cert_info['issuer'] = line.replace('issuer=', '').strip()
        except Exception as e:
            app.logger.error(f'Error reading certificate info: {str(e)}')
            cert_info['error'] = 'Failed to read certificate'

    return jsonify(cert_info)


@app.route('/settings/backup', methods=['POST'])
@admin_required
def trigger_backup():
    """Trigger a backup"""
    if g.is_service_call:
        return {'error': 'This endpoint is for users only'}, 403

    try:
        import subprocess
        backup_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backup.py')

        if os.path.exists(backup_script):
            # Run backup script (note: may need sudo for full backup)
            result = subprocess.run(
                ['python3', backup_script, '--dry-run'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                flash('Backup dry-run completed. Run with sudo for full backup.', 'info')
            else:
                flash(f'Backup check failed: {result.stderr}', 'error')
        else:
            flash('Backup script not found.', 'error')

    except Exception as e:
        app.logger.error(f'Error running backup: {str(e)}')
        flash('Internal server error', 'error')

    return redirect(url_for('settings'))
