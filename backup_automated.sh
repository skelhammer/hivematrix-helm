#!/bin/bash
#
# HiveMatrix Automated Backup Script
# Runs daily backup with retention policy
#
# Usage:
#   sudo ./backup_automated.sh
#
# This script should be run as root via cron for proper database access
#

set -e

# Configuration
BACKUP_DIR="/var/backups/hivematrix"
RETENTION_DAILY=7       # Keep 7 daily backups
RETENTION_WEEKLY=4      # Keep 4 weekly backups (Sunday backups)
RETENTION_MONTHLY=12    # Keep 12 monthly backups (1st of month)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BACKUP_DIR/backup.log"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
chmod 750 "$BACKUP_DIR"

# Check if running as root
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

log "=========================================="
log "HiveMatrix Automated Backup Started"
log "=========================================="

# Determine backup type based on date
DAY_OF_WEEK=$(date +%u)   # 1=Monday, 7=Sunday
DAY_OF_MONTH=$(date +%d)

if [ "$DAY_OF_MONTH" = "01" ]; then
    BACKUP_TYPE="monthly"
    BACKUP_SUBDIR="$BACKUP_DIR/monthly"
    RETENTION=$RETENTION_MONTHLY
elif [ "$DAY_OF_WEEK" = "7" ]; then
    BACKUP_TYPE="weekly"
    BACKUP_SUBDIR="$BACKUP_DIR/weekly"
    RETENTION=$RETENTION_WEEKLY
else
    BACKUP_TYPE="daily"
    BACKUP_SUBDIR="$BACKUP_DIR/daily"
    RETENTION=$RETENTION_DAILY
fi

log "Backup type: $BACKUP_TYPE"
log "Output directory: $BACKUP_SUBDIR"

# Run the backup
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "pyenv" ]; then
    source pyenv/bin/activate
else
    log "ERROR: Virtual environment not found at $SCRIPT_DIR/pyenv"
    exit 1
fi

# Run backup script
log "Running backup.py..."
if python3 backup.py "$BACKUP_SUBDIR"; then
    log "${GREEN}✓ Backup completed successfully${NC}"
    BACKUP_SUCCESS=true
else
    log "${RED}✗ Backup failed${NC}"
    BACKUP_SUCCESS=false
fi

# Get the latest backup file
LATEST_BACKUP=$(ls -t "$BACKUP_SUBDIR"/hivematrix_backup_*.zip 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ] && [ "$BACKUP_SUCCESS" = true ]; then
    BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    log "Backup file: $LATEST_BACKUP ($BACKUP_SIZE)"

    # Verify backup integrity
    log "Verifying backup integrity..."
    if unzip -t "$LATEST_BACKUP" > /dev/null 2>&1; then
        log "${GREEN}✓ Backup integrity verified${NC}"
    else
        log "${RED}✗ Backup integrity check failed!${NC}"
        BACKUP_SUCCESS=false
    fi
fi

# Apply retention policy - remove old backups
if [ "$BACKUP_SUCCESS" = true ]; then
    log "Applying retention policy (keep $RETENTION $BACKUP_TYPE backups)..."

    # Count backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_SUBDIR"/hivematrix_backup_*.zip 2>/dev/null | wc -l)
    log "Current backup count: $BACKUP_COUNT"

    if [ "$BACKUP_COUNT" -gt "$RETENTION" ]; then
        # Remove oldest backups beyond retention
        REMOVE_COUNT=$((BACKUP_COUNT - RETENTION))
        log "Removing $REMOVE_COUNT old backup(s)..."

        ls -t "$BACKUP_SUBDIR"/hivematrix_backup_*.zip | tail -n "$REMOVE_COUNT" | while read old_backup; do
            log "  Removing: $(basename "$old_backup")"
            rm -f "$old_backup"
        done

        log "${GREEN}✓ Retention policy applied${NC}"
    else
        log "No old backups to remove"
    fi
fi

# Calculate total backup disk usage
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Total backup disk usage: $TOTAL_SIZE"

# Summary
log "=========================================="
if [ "$BACKUP_SUCCESS" = true ]; then
    log "${GREEN}✓ Automated backup completed successfully${NC}"
    EXIT_CODE=0
else
    log "${RED}✗ Automated backup failed${NC}"
    EXIT_CODE=1
fi
log "=========================================="
log ""

# Optional: Send notification (email, webhook, etc.)
# Uncomment and configure as needed:
# if [ "$BACKUP_SUCCESS" = false ]; then
#     echo "HiveMatrix backup failed on $(hostname)" | mail -s "Backup Failed" admin@example.com
# fi

exit $EXIT_CODE
