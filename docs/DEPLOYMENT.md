# USB Drop Campaign Manager - Deployment Guide

Complete guide for deploying the USB Drop Campaign Management System on a VPS.

## Prerequisites

- **VPS**: 8GB+ RAM, 2+ CPU cores, 40GB+ disk (Debian 12/13 recommended)
- **Docker**: Docker Engine and Docker Compose v2+
- **Domains**: Two domains pointed to your VPS IP:
  - App domain (e.g., `app.yourdomain.com`, `api.yourdomain.com`)
  - Canary domain (e.g., `tokens.yourdomain.com`)
- **Ports**: 80 and 443 open for HTTPS traffic
- **Optional**: Cloudflare account for wildcard SSL certificates

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url> usb-drop
cd usb-drop

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Generate Secure Secrets

Run these commands and paste the results into your `.env` file:

```bash
# Database password
openssl rand -hex 32

# JWT secret key
openssl rand -hex 32

# CanaryTokens factory auth
openssl rand -hex 32

# Redis password
openssl rand -hex 32

# Shlink API key
openssl rand -hex 32

# Shlink database password
openssl rand -hex 16
```

### 3. Configure Environment Variables

Edit `.env` with your settings:

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VPS_IP` | Your server's public IP address | `203.0.113.50` |
| `CANARY_DOMAIN` | Domain for CanaryTokens | `yourdomain.com` |
| `APP_DOMAIN` | Domain for Campaign Manager | `yourdomain.com` |
| `DB_PASSWORD` | PostgreSQL password | (generated) |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (generated) |
| `REDIS_PASSWORD` | Redis password | (generated) |
| `FACTORY_AUTH` | CanaryTokens factory auth token | (generated) |
| `WEBHOOK_URL` | URL for CanaryTokens alerts callback | `https://api.yourdomain.com/api/webhooks/canary` |
| `ADMIN_USERNAME` | Initial admin username | `admin` |
| `ADMIN_EMAIL` | Initial admin email | `admin@yourdomain.com` |
| `ADMIN_PASSWORD` | Initial admin password | (see requirements below) |

#### Password Requirements

The admin password must meet these requirements:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*etc.)

#### Conditional Variables

| Variable | When Required | Description |
|----------|---------------|-------------|
| `CLOUDFLARE_API_TOKEN` | For wildcard SSL | DNS-01 challenge for `*.yourdomain.com` |
| `GOOGLE_API_KEY` | For Google Docs tokens | Enable Docs API in Google Cloud Console |

#### Optional Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | AI content/image generation |
| `SLACK_WEBHOOK_URL` | Slack alert notifications |
| `IPINFO_TOKEN` | IP geolocation in alerts |
| `MAILGUN_API_KEY` | Email notifications via Mailgun |
| `SENDGRID_API_KEY` | Email notifications via SendGrid |
| `GEOLITE_LICENSE_KEY` | MaxMind GeoLite2 for Shlink stats |
| `WG_PRIVATE_KEY_SEED` | WireGuard token support |

#### JWT Configuration (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

#### Example .env

```bash
# Server
VPS_IP=203.0.113.50
CANARY_DOMAIN=yourdomain.com
APP_DOMAIN=yourdomain.com

# Database
DB_PASSWORD=a1b2c3d4e5f6...

# Authentication
JWT_SECRET_KEY=f6e5d4c3b2a1...
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=SecureP@ssw0rd123!

# CanaryTokens
FACTORY_AUTH=1a2b3c4d5e6f...
WEBHOOK_URL=https://api.yourdomain.com/api/webhooks/canary

# Redis
REDIS_PASSWORD=9f8e7d6c5b4a...

# Optional
OPENAI_API_KEY=sk-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
IPINFO_TOKEN=abc123...
CLOUDFLARE_API_TOKEN=...
```

### 4. Deploy CanaryTokens

```bash
# Start CanaryTokens stack
docker compose -f docker-compose.canarytokens.yml up -d

# Wait for services to be ready (check logs)
docker compose -f docker-compose.canarytokens.yml logs -f

# Verify it's running
docker compose -f docker-compose.canarytokens.yml ps
```

### 5. Deploy Campaign Manager

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f api
```

### 6. Verify Deployment

```bash
# Check all containers are running
docker ps

# Test API health endpoint
curl -s https://api.yourdomain.com/health | jq

# Test CanaryTokens connectivity (from API container)
docker exec usb-drop-api-1 curl -s http://canarytokens-frontend:8082/generate

# Check for errors in logs
docker compose logs api --tail 50
```

### 7. Access the Application

| Service | URL |
|---------|-----|
| Campaign Manager | `https://app.yourdomain.com` |
| API | `https://api.yourdomain.com` |
| CanaryTokens | `https://tokens.yourdomain.com` (basic auth) |
| Landing Pages | `https://rick.yourdomain.com` (and other themes) |
| Short URLs | `https://links.yourdomain.com` |
| Shlink Admin | `https://shlink-admin.yourdomain.com` (basic auth) |

Login with your `ADMIN_USERNAME` and `ADMIN_PASSWORD`.

### 8. Generate API Key (for CLI)

1. Login to the Campaign Manager web UI
2. Navigate to **Settings** → **API Keys**
3. Click **Generate New Key**
4. Copy and save the key securely (it won't be shown again)

## DNS Configuration

Add these DNS records for your domain:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| A | `@` | VPS_IP | Root domain (CanaryTokens triggers) |
| A | `app` | VPS_IP | Campaign Manager frontend |
| A | `api` | VPS_IP | Campaign Manager API |
| A | `tokens` | VPS_IP | CanaryTokens web interface |
| A | `rick` | VPS_IP | Landing page (rickroll theme) |
| A | `links` | VPS_IP | Shlink URL shortener |
| A | `shlink-admin` | VPS_IP | Shlink admin interface |
| A | `www` | VPS_IP | Redirect to app |
| A | `*` | VPS_IP | Wildcard for CanaryTokens callbacks |

**Note:** The wildcard record (`*`) requires a wildcard SSL certificate. See [Cloudflare Wildcard SSL](#cloudflare-wildcard-ssl-optional) section.

## Services and Ports

| Service | Container Name | Internal Port | Description |
|---------|----------------|---------------|-------------|
| API | `usb-drop-api-1` | 8000 | FastAPI backend |
| Frontend | `usb-drop-campaign-frontend-1` | 80 | Vue.js application |
| PostgreSQL | `usb-drop-postgres-1` | 5432 | Primary database |
| Caddy | `usb-drop-caddy-1` | 80, 443 | Reverse proxy (only exposed service) |
| Redis | `canarytokens-redis-1` | 6379 | CanaryTokens cache |
| CanaryTokens Frontend | `canarytokens-frontend-1` | 8082 | Token generation UI |
| CanaryTokens Switchboard | `canarytokens-switchboard-1` | 8083 | Token trigger handler |
| Shlink | `usb-drop-shlink-1` | 8080 | URL shortener |
| Landing Pages | `usb-drop-rickroll-1` | 8080 | Redirect pages |

## Basic Auth Setup

The CanaryTokens UI and Shlink admin are protected with basic authentication.

### Generate Password Hash

```bash
# Generate a bcrypt hash for your password
docker exec usb-drop-caddy-1 caddy hash-password

# Enter your password when prompted
# Copy the output hash
```

### Configure in .env

```bash
TOKENS_BASIC_AUTH_USER=admin
TOKENS_BASIC_AUTH_HASH=$2a$14$YourGeneratedHashHere...
```

### Apply Changes

```bash
docker compose restart caddy
```

## URL Shortener (Shlink)

Shlink creates custom short URLs that redirect to CanaryToken trigger URLs, making them more believable.

### Configuration

1. Add Shlink settings to `.env`:

```bash
SHLINK_DOMAIN=links.yourdomain.com
SHLINK_API_KEY=your-secure-api-key
SHLINK_DB_PASSWORD=secure-shlink-db-password
```

2. Create the Shlink database:

```bash
docker compose exec postgres psql -U usbdrop -d postgres -c "CREATE USER shlink WITH PASSWORD 'your-password';"
docker compose exec postgres psql -U usbdrop -d postgres -c "CREATE DATABASE shlink OWNER shlink;"
```

3. Restart Shlink:

```bash
docker compose restart shlink
```

### Settings Page

Access Settings at `https://app.yourdomain.com/settings` (admin-only) to:

- View Shlink connection status
- Test the Shlink API connection
- Configure URL shortening per profile:
  - **Enable/Disable** - Toggle short URL generation
  - **Base Slug** - Prefix for short URLs (e.g., `hr-docs`)
  - **Suffix Mode**:
    - `random` - Random alphanumeric (e.g., `hr-docs-a7k2`)
    - `drive_code` - Uses drive code (e.g., `hr-docs-usba1b2`)
    - `sequential` - Sequential numbers
    - `custom` - Manually specified
  - **Suffix Length** - Length of random suffix (2-12 characters)

### Example Short URLs

With base slug `hr-docs` and random suffix mode:
```
https://links.yourdomain.com/hr-docs-a7k2
https://links.yourdomain.com/hr-docs-m9p4
```

## Landing Pages

The system includes 11 themed redirect pages that display briefly before redirecting to a target URL. These pages log visitor information (IP, user agent, referer) for reporting.

### Available Themes

| Theme | Description | Subdomain |
|-------|-------------|-----------|
| `corporate` | Generic corporate page | `corp.yourdomain.com` |
| `login` | Fake login redirect | `login.yourdomain.com` |
| `maintenance` | Site maintenance notice | `maint.yourdomain.com` |
| `helpdesk` | IT helpdesk portal | `help.yourdomain.com` |
| `hrportal` | HR portal redirect | `hr.yourdomain.com` |
| `fileshare` | File sharing service | `files.yourdomain.com` |
| `training` | Training portal | `training.yourdomain.com` |
| `banking` | Banking redirect | `bank.yourdomain.com` |
| `document` | Document viewer | `docs.yourdomain.com` |
| `survey` | Survey redirect | `survey.yourdomain.com` |
| `rickroll` | Classic rickroll | `rick.yourdomain.com` |

### Configuration

Each campaign can specify:
- Landing page theme
- Redirect delay (1-30 seconds)
- Target redirect URL

## Cloudflare Wildcard SSL (Optional)

CanaryTokens callbacks use random subdomains (e.g., `abc123.yourdomain.com`). To support these, you need a wildcard SSL certificate.

### Setup

1. Create a Cloudflare API token:
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Create token with **Zone:DNS:Edit** permissions for your domain

2. Add to `.env`:

```bash
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

3. Uncomment the wildcard block in `Caddyfile`:

```
*.yourdomain.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy canarytokens-frontend:8082
}
```

4. Restart Caddy:

```bash
docker compose restart caddy
```

### Verify Certificate

```bash
docker exec usb-drop-caddy-1 caddy list-certificates
```

## SSL/TLS

Caddy automatically obtains and renews Let's Encrypt certificates. No manual configuration needed for standard (non-wildcard) certificates.

### Certificate Locations

Certificates are stored in the Caddy data volume and automatically renewed before expiration.

### Troubleshooting SSL

```bash
# Check certificate status
docker exec usb-drop-caddy-1 caddy list-certificates

# View Caddy logs for certificate issues
docker compose logs caddy | grep -i "certificate\|tls\|acme"

# Force certificate renewal
docker compose restart caddy
```

## Health Checks

### API Health Endpoint

```bash
curl -s https://api.yourdomain.com/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "canary_tokens": "connected"
}
```

### Container Health

```bash
# Check all container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific service
docker inspect --format='{{.State.Health.Status}}' usb-drop-api-1
```

## Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Run database migrations if needed
docker compose exec api alembic upgrade head

# Verify services are running
docker compose ps
```

## Backup

### Database Backup

```bash
# Create backup with timestamp
docker exec usb-drop-postgres-1 pg_dump -U usbdrop usbdrop > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup_20250107_120000.sql | docker exec -i usb-drop-postgres-1 psql -U usbdrop usbdrop
```

### Volume Backup

```bash
# Backup PostgreSQL data volume
docker run --rm \
  -v usb-drop_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Backup uploads directory
docker cp usb-drop-api-1:/app/uploads ./uploads_backup_$(date +%Y%m%d)
```

### Automated Backup Script

```bash
#!/bin/bash
BACKUP_DIR=/opt/backups
DATE=$(date +%Y%m%d)

# Database
docker exec usb-drop-postgres-1 pg_dump -U usbdrop usbdrop > $BACKUP_DIR/db_$DATE.sql

# Uploads
docker cp usb-drop-api-1:/app/uploads $BACKUP_DIR/uploads_$DATE

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete
```

## Troubleshooting

### Check Service Logs

```bash
# API logs
docker compose logs api --tail 100

# Frontend logs
docker compose logs campaign-frontend --tail 50

# Caddy logs
docker compose logs caddy --tail 50

# CanaryTokens logs
docker compose -f docker-compose.canarytokens.yml logs frontend --tail 50
```

### Restart Services

```bash
# Restart specific service
docker compose restart api
docker compose restart campaign-frontend

# Restart all services
docker compose restart
```

### Database Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker exec usb-drop-postgres-1 pg_isready -U usbdrop

# Connect to database
docker exec -it usb-drop-postgres-1 psql -U usbdrop -d usbdrop

# View recent drives
docker exec usb-drop-postgres-1 psql -U usbdrop -d usbdrop \
  -c "SELECT unique_code, status, created_at FROM drives ORDER BY created_at DESC LIMIT 10;"
```

### Reset Database

```bash
# WARNING: This deletes all data!
docker compose down
docker volume rm usb-drop_postgres_data
docker compose up -d
```

### CanaryTokens Not Responding

```bash
# Check CanaryTokens container status
docker compose -f docker-compose.canarytokens.yml ps

# View logs
docker compose -f docker-compose.canarytokens.yml logs frontend

# Test internal connectivity from API
docker exec usb-drop-api-1 curl -v http://canarytokens-frontend:8082/generate
```

### Token Creation Fails

1. Verify `FACTORY_AUTH` matches in both `.env` files
2. Check `WEBHOOK_URL` is accessible from the internet
3. Ensure CanaryTokens frontend container is running
4. Check API logs: `docker compose logs api --tail 100`

### Webhooks Not Receiving Alerts

```bash
# Test webhook endpoint directly
curl -X POST https://api.yourdomain.com/api/webhooks/canary \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Verify WEBHOOK_URL in API container
docker compose exec api printenv | grep WEBHOOK

# Check Redis for token webhook config
docker compose -f docker-compose.canarytokens.yml exec redis redis-cli
KEYS canarydrop:*
GET canarydrop:<token-id>  # Should show alert_webhook_enabled: True
```

### Drive Download Returns Empty ZIP

```bash
# Check drive manifest in database
docker exec usb-drop-postgres-1 psql -U usbdrop -d usbdrop \
  -c "SELECT files_manifest FROM drives WHERE unique_code = 'USB-XXXXXX';"

# Check API logs during download
docker compose logs api --tail 100 | grep -i zip
```

### Frontend Caching Issues

If the frontend shows outdated content after updates:

```bash
# Rebuild frontend with no cache
docker compose build --no-cache campaign-frontend
docker compose up -d campaign-frontend

# Clear browser cache or test in incognito mode
```

If external caching persists (CDN, hosting provider cache):
- Wait for cache TTL to expire
- Contact hosting provider to purge cache
- Add cache-busting query parameters temporarily

## Security Considerations

1. **Change Default Credentials**: Always change the default admin password
2. **Firewall**: Only expose ports 80 and 443
3. **Basic Auth**: Protect CanaryTokens and Shlink admin interfaces
4. **Updates**: Regularly update Docker images
5. **Backups**: Schedule regular database backups
6. **Monitoring**: Set up log monitoring for security events
7. **API Keys**: Rotate API keys periodically
8. **HTTPS Only**: All traffic should use HTTPS (enforced by Caddy)

## Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h

# View container resource limits
docker inspect usb-drop-api-1 --format='{{.HostConfig.Memory}}'
```

## Architecture

```
                         Internet
                             |
                         [Caddy]
                        /   |   \
                       /    |    \
           [Frontend] [API] [Landing Pages]
                       |
                  [PostgreSQL]
                       |
    +------------------+------------------+
    |                  |                  |
[Shlink]    [CanaryTokens Frontend]  [CanaryTokens Switchboard]
    |                  |                  |
    +------------ [Redis] ---------------+
```

All services communicate through an internal Docker network. Only Caddy is exposed to the internet on ports 80 and 443.

### Network Flow

1. **User Request** → Caddy (HTTPS termination) → Frontend/API
2. **Token Trigger** → Caddy → CanaryTokens Switchboard → Webhook → API
3. **Short URL** → Caddy → Shlink → Redirect to CanaryToken URL
4. **Landing Page** → Caddy → Landing Page Service → Log & Redirect
