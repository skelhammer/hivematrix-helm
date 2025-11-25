# HiveMatrix Helm

Service orchestration and management dashboard for HiveMatrix.

## Overview

Helm is the control center for HiveMatrix - it manages all services, monitors system health, and provides the admin dashboard for the platform.

**Port:** 5004

## Features

- **Service Management** - Start, stop, restart all HiveMatrix services
- **Health Monitoring** - Real-time status of all services and dependencies
- **Log Aggregation** - Centralized logging from all services
- **Database Management** - PostgreSQL connection management
- **Keycloak Integration** - User and realm management
- **Systemd Support** - Production deployment with systemd service

## Tech Stack

- Flask + Gunicorn
- PostgreSQL
- SQLAlchemy ORM

## Installation

### Prerequisites

Install all system dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql nginx certbot python3-certbot-nginx
```

### First Time Setup

```bash
# Clone all HiveMatrix repos (if not already done)
cd /path/to/hivematrix
for repo in hivematrix-core hivematrix-nexus hivematrix-beacon hivematrix-codex hivematrix-knowledgetree hivematrix-ledger hivematrix-helm hivematrix-brainhair; do
    git clone git@github.com:yourorg/$repo.git
done

# Run Helm installer
cd hivematrix-helm
./install.sh
```

### Quick Start (Development)

```bash
source pyenv/bin/activate
python cli.py start all
```

## Starting and Stopping Services

### Start All Services

```bash
./start.sh
```

### Stop All Services

```bash
./stop.sh
```

## Systemd Service Management

### Install the Systemd Service

**Note:** Run `./start.sh` at least once before installing the systemd service to complete initial setup.

```bash
./install_autostart.sh
```

### Uninstall the Systemd Service

```bash
./uninstall_autostart.sh
```

### Start the Systemd Service

```bash
sudo systemctl start hivematrix
```

### Stop the Systemd Service

```bash
sudo systemctl stop hivematrix
```

### Check Service Status

```bash
sudo systemctl status hivematrix
```

### View Logs

```bash
sudo journalctl -u hivematrix -f
```

## Updating HiveMatrix

### Stop Services Before Updating

```bash
# Stop the systemd service first
sudo systemctl stop hivematrix

# Or if running in dev mode:
./stop.sh
```

### Pull Updates for All Repos

```bash
cd /path/to/hivematrix
for dir in */; do [ -d "$dir/.git" ] && (cd "$dir" && echo "=== $dir ===" && git pull); done
```

### Reinstall a Service After Update

```bash
./install <service_name>

# Examples:
./install ledger
./install beacon
./install codex
```

### Restart Services After Update

```bash
# Production (systemd)
sudo systemctl start hivematrix

# Development
./start.sh
```

## Backup and Restore

### Manual Backup

```bash
# Backup to /tmp (default)
sudo python3 backup.py

# Backup to specific directory
sudo python3 backup.py /path/to/backup/dir

# Test backup without creating files
python3 backup.py --dry-run
```

Backups include PostgreSQL databases, Neo4j databases, and Keycloak configuration.

### Restore from Backup

```bash
# Full restore (all components)
sudo python3 restore.py /path/to/hivematrix_backup_YYYYMMDD_HHMMSS.zip

# Restore specific components only
sudo python3 restore.py backup.zip --postgresql-only
sudo python3 restore.py backup.zip --neo4j-only
sudo python3 restore.py backup.zip --keycloak-only
sudo python3 restore.py backup.zip --configs-only

# Skip confirmation prompts (dangerous!)
sudo python3 restore.py backup.zip --force
```

**Warning:** Restore will OVERWRITE existing data!

### Automated Backups (Cron)

Install automated daily backups:

```bash
./install_backup_cron.sh
```

This creates:
- **Daily backups** at 2 AM (keeps 7 days)
- **Weekly backups** on Sunday (keeps 4 weeks)
- **Monthly backups** on 1st of month (keeps 12 months)

Backup location: `/var/backups/hivematrix/`

View backup logs:

```bash
sudo tail -f /var/backups/hivematrix/backup.log
```

Uninstall automated backups:

```bash
./uninstall_backup_cron.sh
```

## Key Files

- `cli.py` - Command-line service management
- `install_manager.py` - Service installation
- `services.json` - Service registry and configuration

## Environment Variables

- `DEV_MODE` - Enable Flask dev server (default: false)
- `CORE_SERVICE_URL` - Core service URL
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Documentation

For complete installation, configuration, and architecture documentation:

**[HiveMatrix Documentation](https://skelhammer.github.io/hivematrix-docs/)**

## License

MIT License - See LICENSE file
