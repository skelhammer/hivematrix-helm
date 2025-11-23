#!/bin/bash
#
# HiveMatrix Auto-start Uninstallation Script
# Removes HiveMatrix systemd service and disables auto-start
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="hivematrix"
SYSTEM_SERVICE_DIR="/etc/systemd/system"
SERVICE_FILE="$SYSTEM_SERVICE_DIR/${SERVICE_NAME}.service"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "================================================================"
echo "  HiveMatrix Auto-Start Uninstallation"
echo "================================================================"
echo ""

# Check for sudo access
echo -e "${YELLOW}Checking for sudo privileges...${NC}"
if ! sudo -v; then
    echo -e "${RED}⚠️ This script requires sudo access${NC}"
    echo ""
    echo "Please run with sudo privileges or provide your password when prompted."
    exit 1
fi
echo -e "${GREEN}✓ Sudo access confirmed${NC}"
echo ""

# Check if service is installed
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}⚠️  HiveMatrix service not found${NC}"
    echo ""
    echo "The systemd service does not appear to be installed."
    echo "Nothing to uninstall."
    echo ""
    exit 0
fi

echo -e "${GREEN}✓ Found HiveMatrix service${NC}"
echo ""

# Check if service is running
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${YELLOW}Stopping HiveMatrix service...${NC}"
    sudo systemctl stop $SERVICE_NAME
    echo -e "${GREEN}✓ Service stopped${NC}"
    echo ""
else
    echo -e "${BLUE}Service is not running${NC}"
    echo ""
fi

# Disable service
if sudo systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo -e "${YELLOW}Disabling HiveMatrix service...${NC}"
    sudo systemctl disable $SERVICE_NAME
    echo -e "${GREEN}✓ Service disabled${NC}"
    echo ""
else
    echo -e "${BLUE}Service is not enabled${NC}"
    echo ""
fi

# Remove service file
echo -e "${YELLOW}Removing service file...${NC}"
sudo rm -f "$SERVICE_FILE"
echo -e "${GREEN}✓ Service file removed${NC}"
echo ""

# Reload systemd
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"
echo ""

# Reset failed state (if any)
sudo systemctl reset-failed 2>/dev/null || true

echo "================================================================"
echo -e "${GREEN}  Uninstallation Complete!${NC}"
echo "================================================================"
echo ""
echo -e "${BLUE}Status:${NC}"
echo "  Auto-start: Disabled"
echo "  Service file: Removed"
echo ""
echo -e "${BLUE}Note:${NC} HiveMatrix is still installed and can be run manually using:"
echo "  cd $SCRIPT_DIR"
echo "  ./start.sh"
echo ""
echo -e "${YELLOW}To reinstall auto-start, run:${NC}"
echo "  ./install_autostart.sh"
echo ""
