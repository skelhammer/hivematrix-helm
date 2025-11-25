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

### System Requirements

**Automatically installed by `start.sh`:**
- Python 3.8+ (python3, python3-pip, python3-venv)
- Git
- Java 17 (OpenJDK) - for Keycloak authentication server
- PostgreSQL - for service databases
- Redis - for Core session storage
- wget, jq

**Manual installation required (optional services):**
- Neo4j 5.x - only required if using KnowledgeTree

### First Time Setup

```bash
# 1. Clone only Helm (it will clone Core, Nexus, Codex automatically)
mkdir hivematrix && cd hivematrix
git clone https://github.com/skelhammer/hivematrix-helm
cd hivematrix-helm

# 2. Run start.sh - this handles everything:
#    - Installs system dependencies (Python, PostgreSQL, Redis, Java, etc.)
#    - Downloads and configures Keycloak
#    - Clones Core, Nexus, and Codex
#    - Creates Python virtual environments
#    - Sets up databases
#    - Generates SSL certificates
#    - Starts all required services
./start.sh
```

That's it! The `start.sh` script is a complete installer and launcher.

### Installing Additional Services

Additional services (Beacon, Ledger, Brainhair, KnowledgeTree) can be added after initial setup:

```bash
# Clone any additional services you need
cd /path/to/hivematrix
git clone https://github.com/skelhammer/hivematrix-beacon
git clone https://github.com/skelhammer/hivematrix-ledger
git clone https://github.com/skelhammer/hivematrix-brainhair
git clone https://github.com/skelhammer/hivematrix-knowledgetree  # Requires Neo4j

# Run start.sh again - it auto-detects and installs new services
cd hivematrix-helm
./start.sh
```

### Quick Start (after initial setup)

```bash
./start.sh
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
