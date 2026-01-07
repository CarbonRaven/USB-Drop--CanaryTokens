# USB Drop Campaign Manager - Deployment Guide

## Prerequisites

- VPS with at least 8GB RAM (Debian 13 recommended)
- Docker and Docker Compose installed
- Two domains pointed to your VPS IP:
  - `subproject55.com` - for CanaryTokens and Campaign Manager

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url> usb-drop-system
cd usb-drop-system

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Required settings
VPS_IP=your.server.ip
DB_PASSWORD=secure-database-password
JWT_SECRET=secure-random-string-for-jwt
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password

# CanaryTokens
CANARY_DOMAIN=subproject55.com
FACTORY_AUTH=random-auth-token-for-canary-api

# Optional: OpenAI for AI content generation
OPENAI_API_KEY=sk-your-openai-key

# Webhook URL for CanaryTokens alerts (required for alerts to work)
WEBHOOK_URL=https://api.subproject55.com/api/webhooks/canary

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 3. Deploy CanaryTokens

```bash
# Start CanaryTokens stack
docker compose -f docker-compose.canarytokens.yml up -d

# Verify it's running
docker compose -f docker-compose.canarytokens.yml ps
```

### 4. Deploy Campaign Manager

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Initialize Database

The database will be automatically initialized on first run. An admin user will be created with the credentials from your `.env` file.

### 6. Access the Application

- Campaign Manager: `https://app.subproject55.com`
- API: `https://api.subproject55.com`
- CanaryTokens: `https://tokens.subproject55.com`
- RickRoll Landing: `https://rick.subproject55.com`

## DNS Configuration

Add the following DNS records for your domain:

### subproject55.com
```
A     @           -> VPS_IP
A     app         -> VPS_IP
A     api         -> VPS_IP
A     tokens      -> VPS_IP
A     rick        -> VPS_IP
A     *           -> VPS_IP  (wildcard for custom landing pages)
```

## URL Shortener (Shlink)

The system includes Shlink for creating custom short URLs that redirect to CanaryToken trigger URLs.

### Configuration

1. Add Shlink settings to `.env`:
```bash
SHLINK_DOMAIN=links.subproject55.com
SHLINK_API_KEY=your-secure-api-key
SHLINK_DB_PASSWORD=secure-shlink-db-password
```

2. Add DNS record:
```
A     links       -> VPS_IP
```

3. Create the Shlink database:
```bash
docker compose exec postgres psql -U usbdrop -d postgres -c "CREATE USER shlink WITH PASSWORD 'your-password';"
docker compose exec postgres psql -U usbdrop -d postgres -c "CREATE DATABASE shlink OWNER shlink;"
```

4. Restart Shlink:
```bash
docker compose restart shlink
```

### Settings Page

Access the Settings page at `https://app.subproject55.com/settings` (admin-only) to:

- View Shlink connection status
- Test the Shlink API connection
- Configure URL shortening for each profile:
  - **Enable/Disable** - Toggle short URL generation per profile
  - **Base Slug** - Prefix for short URLs (e.g., `hr-docs`)
  - **Suffix Mode** - How the unique suffix is generated:
    - `random` - Random alphanumeric (e.g., `hr-docs-a7k2`)
    - `drive_code` - Uses drive code (e.g., `hr-docs-usba1b2`)
    - `sequential` - Sequential numbers
    - `custom` - Manually specified
  - **Suffix Length** - Length of random suffix (2-12 characters)

### Example Short URLs

With base slug `hr-docs` and random suffix mode:
```
https://links.subproject55.com/hr-docs-a7k2
https://links.subproject55.com/hr-docs-m9p4
```

## SSL/TLS

Caddy automatically obtains and renews Let's Encrypt certificates. No manual configuration needed.

## Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Run migrations if needed
docker compose exec api alembic upgrade head
```

## Backup

### Database Backup
```bash
# Create backup
docker compose exec postgres pg_dump -U usbdrop usbdrop > backup.sql

# Restore backup
cat backup.sql | docker compose exec -T postgres psql -U usbdrop usbdrop
```

### Volume Backup
```bash
# Backup all volumes
docker run --rm -v usb-drop-system_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Troubleshooting

### Check Service Logs
```bash
docker compose logs api
docker compose logs frontend
docker compose logs caddy
```

### Restart Services
```bash
docker compose restart api
docker compose restart frontend
```

### Reset Database
```bash
docker compose down
docker volume rm usb-drop-system_postgres_data
docker compose up -d
```

### Check Caddy Certificates
```bash
docker compose exec caddy caddy list-certificates
```

### Frontend Caching Issues
If the frontend is showing outdated content after updates:

1. The frontend nginx config includes no-cache headers for HTML files to prevent stale content
2. Static assets (JS, CSS, images) are cache-busted via content hashes in filenames
3. If you're behind a CDN or network-level cache, you may need to wait for cache expiry (typically 1-24 hours)

Force rebuild and clear caches:
```bash
# Rebuild frontend with no cache
docker compose build --no-cache campaign-frontend
docker compose up -d campaign-frontend

# Clear browser cache or test in incognito mode
```

If external caching persists (CDN, hosting provider cache):
- Wait for cache TTL to expire
- Contact hosting provider to purge cache
- Consider adding cache-busting query parameters temporarily

### Alerts Not Working
If token triggers are not showing in the dashboard:

1. Verify `WEBHOOK_URL` is set in `.env` and in `docker-compose.yml`:
```bash
# Check .env
grep WEBHOOK_URL .env

# Check docker-compose.yml has it in api environment
grep -A 20 "api:" docker-compose.yml | grep WEBHOOK_URL
```

2. Verify the API container has the environment variable:
```bash
docker compose exec api printenv | grep WEBHOOK
```

3. Check if tokens are being created with webhook config:
```bash
# Connect to Redis and check a token
docker compose -f docker-compose.canarytokens.yml exec redis redis-cli
KEYS canarydrop:*
GET canarydrop:<token-id>  # Should show alert_webhook_enabled: True
```

## Security Considerations

1. **Change Default Credentials**: Always change the default admin password
2. **Firewall**: Only expose ports 80 and 443
3. **Updates**: Regularly update Docker images
4. **Backups**: Schedule regular database backups
5. **Monitoring**: Set up log monitoring for security events

## Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h
```

## Architecture

```
                    Internet
                        |
                    [Caddy]
                   /   |   \
                  /    |    \
        [Frontend] [API] [CanaryTokens]
                   |
              [PostgreSQL]
```

All services communicate through an internal Docker network. Only Caddy is exposed to the internet.
