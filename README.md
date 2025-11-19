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

## Quick Start

```bash
# First time setup
./install.sh

# Start all services
./start.sh

# Or use CLI
source pyenv/bin/activate
python cli.py start all
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
