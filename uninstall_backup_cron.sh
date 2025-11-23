#!/bin/bash
#
# Uninstall HiveMatrix Automated Backup Cron Job
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_automated.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "================================================================"
echo "  HiveMatrix Automated Backup Uninstallation"
echo "================================================================"
echo ""

# Check for sudo
if ! sudo -v; then
    echo -e "${RED}⚠️ This script requires sudo access${NC}"
    exit 1
fi

# Check if cron job exists
if ! sudo crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}No automated backup cron job found${NC}"
    echo "Nothing to uninstall"
    exit 0
fi

echo "Current cron job:"
sudo crontab -l | grep "$BACKUP_SCRIPT"
echo ""

read -p "Remove automated backup cron job? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled"
    exit 0
fi

# Remove cron job
sudo crontab -l | grep -v "$BACKUP_SCRIPT" | sudo crontab -

echo -e "${GREEN}✓ Cron job removed${NC}"
echo ""
echo -e "${BLUE}Note:${NC} Existing backups are preserved in /var/backups/hivematrix/"
echo ""
echo "To manually delete backups:"
echo "  sudo rm -rf /var/backups/hivematrix/"
echo ""
echo "To reinstall:"
echo "  ./install_backup_cron.sh"
echo ""
