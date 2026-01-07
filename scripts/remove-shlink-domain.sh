#!/bin/bash
# =============================================================================
# Remove Shlink Domain Script
# Removes a domain from Caddy configuration
# Usage: ./remove-shlink-domain.sh <domain>
# =============================================================================

set -e

CADDYFILE="/home/deploy/usb-drop/Caddyfile"
COMPOSE_DIR="/home/deploy/usb-drop"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if domain argument provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No domain specified${NC}"
    echo "Usage: $0 <domain>"
    exit 1
fi

DOMAIN="$1"

echo -e "${YELLOW}Removing Shlink domain: ${DOMAIN}${NC}"

# Check if domain exists in Caddyfile
if ! grep -q "^${DOMAIN} {" "$CADDYFILE" 2>/dev/null; then
    echo -e "${RED}Error: Domain '${DOMAIN}' not found in Caddyfile${NC}"
    exit 1
fi

# Backup current Caddyfile
BACKUP_FILE="${CADDYFILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CADDYFILE" "$BACKUP_FILE"
echo -e "${GREEN}Backup created: ${BACKUP_FILE}${NC}"

# Remove the domain block (including comment line above if present)
# This handles the format:
# # Shlink domain: example.com (added YYYY-MM-DD)
# example.com {
#     reverse_proxy shlink:8080
# }

# Create temporary file
TEMP_FILE="${CADDYFILE}.tmp"

awk -v domain="$DOMAIN" '
    BEGIN { skip = 0; prev_comment = "" }
    /^# Shlink domain:/ { prev_comment = $0; next }
    $0 ~ "^" domain " \\{" { skip = 1; prev_comment = ""; next }
    skip && /^}$/ { skip = 0; next }
    skip { next }
    {
        if (prev_comment != "") { print prev_comment; prev_comment = "" }
        print
    }
' "$CADDYFILE" > "$TEMP_FILE"

mv "$TEMP_FILE" "$CADDYFILE"

echo -e "${GREEN}Domain removed from Caddyfile${NC}"

# Validate Caddy configuration
echo -e "${YELLOW}Validating Caddy configuration...${NC}"
cd "$COMPOSE_DIR"
if docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile > /dev/null 2>&1; then
    echo -e "${GREEN}Caddy configuration valid${NC}"
else
    echo -e "${RED}Error: Caddy configuration invalid. Restoring backup...${NC}"
    cp "$BACKUP_FILE" "$CADDYFILE"
    exit 1
fi

# Reload Caddy
echo -e "${YELLOW}Reloading Caddy...${NC}"
if docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile; then
    echo -e "${GREEN}Caddy reloaded successfully${NC}"
else
    echo -e "${RED}Error: Failed to reload Caddy${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Domain ${DOMAIN} removed successfully!${NC}"
