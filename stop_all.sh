#!/bin/bash
#
# HiveMatrix Helm - Stop All Services Script
# Cleanly stops all HiveMatrix services in parallel
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "================================================================"
echo "  HiveMatrix Helm - Stopping All Services"
echo "================================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ ! -d "pyenv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    exit 1
fi

source pyenv/bin/activate

echo -e "${BLUE}Stopping all services in parallel...${NC}"
echo ""

# Use associative array to avoid duplicates
declare -A SERVICES_MAP

# Auto-detect all hivematrix services
for dir in "$PARENT_DIR"/hivematrix-*; do
    if [ -d "$dir" ]; then
        service_name=$(basename "$dir" | sed 's/^hivematrix-//')
        if [ -f "$dir/run.py" ]; then
            SERVICES_MAP["$service_name"]=1
        fi
    fi
done

# Add keycloak (not auto-detected since it's not hivematrix-*)
SERVICES_MAP["keycloak"]=1

# Convert to array
SERVICES_TO_STOP=("${!SERVICES_MAP[@]}")

# Stop all services in parallel
PIDS=()
for svc in "${SERVICES_TO_STOP[@]}"; do
    (
        python cli.py stop $svc 2>/dev/null || true
        echo -e "${GREEN}✓ $svc stopped${NC}"
    ) &
    PIDS+=($!)
done

# Wait for all stop commands to finish
for pid in "${PIDS[@]}"; do
    wait $pid
done

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""

# Show final status
echo "================================================================"
echo "  Final Service Status"
echo "================================================================"
python cli.py status

echo ""
echo "================================================================"
echo -e "${GREEN}  All HiveMatrix services have been stopped${NC}"
echo "================================================================"
echo ""
