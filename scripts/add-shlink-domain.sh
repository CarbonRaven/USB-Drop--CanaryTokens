#!/bin/bash
# =============================================================================
# Add Shlink Domain Script
# Adds a new domain to Caddy configuration for Shlink URL shortening
# Usage: ./add-shlink-domain.sh <domain>
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
    echo "Example: $0 short.example.com"
    exit 1
fi

DOMAIN="$1"

# Validate domain format (basic check)
if ! echo "$DOMAIN" | grep -qE '^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'; then
    echo -e "${RED}Error: Invalid domain format${NC}"
    exit 1
fi

echo -e "${YELLOW}Adding Shlink domain: ${DOMAIN}${NC}"

# Check if domain already exists in Caddyfile
if grep -q "^${DOMAIN} {" "$CADDYFILE" 2>/dev/null; then
    echo -e "${RED}Error: Domain '${DOMAIN}' already exists in Caddyfile${NC}"
    exit 1
fi

# Check DNS resolution
echo -e "${YELLOW}Checking DNS resolution...${NC}"
if ! host "$DOMAIN" > /dev/null 2>&1; then
    echo -e "${RED}Warning: DNS lookup failed for ${DOMAIN}${NC}"
    echo "Make sure DNS is configured before proceeding."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    IP=$(dig +short "$DOMAIN" | head -1)
    echo -e "${GREEN}DNS OK: ${DOMAIN} -> ${IP}${NC}"
fi

# Backup current Caddyfile
BACKUP_FILE="${CADDYFILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CADDYFILE" "$BACKUP_FILE"
echo -e "${GREEN}Backup created: ${BACKUP_FILE}${NC}"

# Add new domain configuration before the wildcard section (or at end if no wildcard)
# Look for the "# Wildcard" comment or end of file
NEW_CONFIG="
# Shlink domain: ${DOMAIN} (added $(date +%Y-%m-%d))
${DOMAIN} {
    reverse_proxy shlink:8080
}
"

# Find the line number of the wildcard section or use end of file
if grep -n "# ===.*Wildcard" "$CADDYFILE" > /dev/null 2>&1; then
    # Insert before wildcard section
    LINE_NUM=$(grep -n "# ===.*Wildcard" "$CADDYFILE" | head -1 | cut -d: -f1)
    head -n $((LINE_NUM - 1)) "$CADDYFILE" > "${CADDYFILE}.tmp"
    echo "$NEW_CONFIG" >> "${CADDYFILE}.tmp"
    tail -n +$LINE_NUM "$CADDYFILE" >> "${CADDYFILE}.tmp"
    mv "${CADDYFILE}.tmp" "$CADDYFILE"
else
    # Append to end of file
    echo "$NEW_CONFIG" >> "$CADDYFILE"
fi

echo -e "${GREEN}Domain added to Caddyfile${NC}"

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

# Reload Caddy to apply changes and get SSL certificate
echo -e "${YELLOW}Reloading Caddy (this will provision SSL certificate)...${NC}"
if docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile; then
    echo -e "${GREEN}Caddy reloaded successfully${NC}"
else
    echo -e "${RED}Error: Failed to reload Caddy. Check logs with: docker compose logs caddy${NC}"
    exit 1
fi

# Wait a moment for SSL provisioning
echo -e "${YELLOW}Waiting for SSL certificate provisioning...${NC}"
sleep 5

# Test HTTPS access
echo -e "${YELLOW}Testing HTTPS access...${NC}"
if curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${DOMAIN}/" | grep -qE "^(200|301|302|404)$"; then
    echo -e "${GREEN}HTTPS is working for ${DOMAIN}${NC}"
else
    echo -e "${YELLOW}Warning: HTTPS test inconclusive. Certificate may still be provisioning.${NC}"
    echo "Check status with: curl -I https://${DOMAIN}/"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Domain ${DOMAIN} added successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Short URLs can now use: https://${DOMAIN}/<slug>"
echo ""
echo "To use this domain in Shlink, you can now add it via the Settings page"
echo "or create short URLs with domain='${DOMAIN}'"
