#!/bin/bash
#
# Install HiveMatrix Automated Backup Cron Job
# Runs daily at 2 AM
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_automated.sh"
CRON_TIME="0 2 * * *"  # 2 AM daily

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "================================================================"
echo "  HiveMatrix Automated Backup Installation"
echo "================================================================"
echo ""

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}ERROR: Backup script not found: $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Check for sudo
if ! sudo -v; then
    echo -e "${YELLOW}⚠️ This script requires sudo access${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing automated backup cron job...${NC}"

# Create cron job for root user
CRON_JOB="$CRON_TIME $BACKUP_SCRIPT >> /var/backups/hivematrix/backup.log 2>&1"

# Check if cron job already exists
if sudo crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${BLUE}  Cron job already installed${NC}"
    echo ""
    echo "Current cron job:"
    sudo crontab -l | grep "$BACKUP_SCRIPT"
    echo ""
    read -p "Replace existing cron job? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi

    # Remove existing cron job
    sudo crontab -l | grep -v "$BACKUP_SCRIPT" | sudo crontab -
    echo -e "${GREEN}✓ Removed old cron job${NC}"
fi

# Add new cron job
(sudo crontab -l 2>/dev/null; echo "$CRON_JOB") | sudo crontab -

echo -e "${GREEN}✓ Cron job installed${NC}"
echo ""

# Create backup directory
sudo mkdir -p /var/backups/hivematrix/{daily,weekly,monthly}
echo -e "${GREEN}✓ Created backup directories${NC}"
echo ""

echo "================================================================"
echo -e "${GREEN}  Installation Complete!${NC}"
echo "================================================================"
echo ""
echo -e "${BLUE}Backup Schedule:${NC}"
echo "  Daily:   2:00 AM (keeps 7 days)"
echo "  Weekly:  2:00 AM Sunday (keeps 4 weeks)"
echo "  Monthly: 2:00 AM 1st of month (keeps 12 months)"
echo ""
echo -e "${BLUE}Backup Location:${NC}"
echo "  /var/backups/hivematrix/"
echo "    ├── daily/    (last 7 days)"
echo "    ├── weekly/   (last 4 weeks)"
echo "    └── monthly/  (last 12 months)"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  /var/backups/hivematrix/backup.log"
echo ""
echo -e "${BLUE}View Cron Job:${NC}"
echo "  sudo crontab -l"
echo ""
echo -e "${BLUE}Test Backup Now:${NC}"
echo "  sudo $BACKUP_SCRIPT"
echo ""
echo -e "${BLUE}View Logs:${NC}"
echo "  sudo tail -f /var/backups/hivematrix/backup.log"
echo ""
echo -e "${YELLOW}To uninstall:${NC}"
echo "  ./uninstall_backup_cron.sh"
echo ""
