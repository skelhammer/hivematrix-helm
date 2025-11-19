#!/bin/bash
#
# HiveMatrix systemd stop script
# Stops all HiveMatrix services gracefully in parallel
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

echo "Stopping HiveMatrix services..."

# Activate virtual environment
source pyenv/bin/activate 2>/dev/null || true

# Use associative array to avoid duplicates
declare -A SERVICES_MAP

# Auto-detect all hivematrix services
for dir in "$SCRIPT_DIR"/../hivematrix-*; do
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
        python cli.py stop "$svc" 2>/dev/null || true
        echo -e "${GREEN}✓ $svc stopped${NC}"
    ) &
    PIDS+=($!)
done

# Wait for all stop commands to finish
for pid in "${PIDS[@]}"; do
    wait $pid
done

echo "All services stopped."
