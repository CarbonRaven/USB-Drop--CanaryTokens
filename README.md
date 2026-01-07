# USB Drop Campaign Management System

A comprehensive platform for managing USB drop penetration testing campaigns with integrated CanaryTokens, real-time alerting, and AI-generated content.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

This system streamlines USB drop security assessments by providing:

- **Automated Token Generation** - Integration with self-hosted CanaryTokens for DNS, Word, Excel, PDF, and other token types
- **Campaign Management** - Organize drives by client, track deployment locations, and monitor trigger events
- **USB Profiles** - Reusable templates with AI-generated content (documents, images) for realistic scenarios
- **Real-time Alerts** - WebSocket-based notifications with Slack integration
- **Geographic Tracking** - Interactive map visualization of deployment locations (blue) and trigger events (red) with detailed popups
- **CLI Tool** - Command-line interface for field operators preparing and deploying drives

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

All services run in Docker containers on a single VPS with Caddy providing automatic HTTPS.

## Features

### Campaign Manager Web UI
- Dashboard with real-time statistics
- Campaign and profile management
- **12 pre-configured scenario profiles** with AI-generated images
- Drive preparation wizard with automatic token and image inclusion
- Interactive map with deployment/trigger markers
- Alert feed with filtering
- Editable deployment details (even after triggers are received)
- Campaign reports with charts and CSV export
- **Settings page** for Shlink URL shortener configuration (admin-only)
- **URL shortening** with customizable slugs per profile
- **Unique URLs per link** - Each URL placeholder in text files gets a unique short URL for believability

### CLI Tool
- Interactive and scripted modes
- Direct USB drive writing
- Batch drive preparation
- Field deployment recording with GPS

### Landing Pages
- **11 themed redirect pages**: corporate, login, maintenance, helpdesk, hrportal, fileshare, training, banking, document, survey, onlyfans
- Per-campaign configuration with preview links
- **Configurable redirect delay** (1-30 seconds) per campaign
- Visitor logging (IP, user agent, referer) before redirect
- Configurable target URLs via environment variables

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python 3.11+) |
| Frontend | Vue 3 + Vite + Tailwind CSS |
| Database | PostgreSQL 16 |
| Container Orchestration | Docker Compose |
| CanaryTokens | Self-hosted Docker deployment |
| Reverse Proxy | Caddy (automatic HTTPS) |
| AI Generation | OpenAI API (GPT-4 + DALL-E 3) |
| Maps | Leaflet.js + OpenStreetMap |
| Real-time | WebSockets |

## Quick Start

### Prerequisites

- VPS with 8GB+ RAM (Debian 13 recommended)
- Docker and Docker Compose v2+
- **Two domains** pointed to your VPS:
  - **App domain** (e.g., `app.example.com`, `api.example.com`) - Campaign Manager
  - **Canary domain** (e.g., `tokens.example.com`) - CanaryTokens server

### 1. Clone and Configure

```bash
git clone https://github.com/CarbonRaven/USB-Drop--CanaryTokens.git
cd USB-Drop--CanaryTokens

# Copy and edit environment configuration
cp .env.example .env
nano .env
```

### 2. Configure Required Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VPS_IP` | Yes | Your server's public IP address |
| `DB_PASSWORD` | Yes | PostgreSQL database password |
| `JWT_SECRET_KEY` | Yes | Secret for JWT tokens (use `openssl rand -hex 32`) |
| `ADMIN_USERNAME` | Yes | Initial admin account username |
| `ADMIN_PASSWORD` | Yes | Initial admin account password |
| `CANARY_DOMAIN` | Yes | Domain for CanaryTokens (e.g., `tokens.example.com`) |
| `FACTORY_AUTH` | Yes | CanaryTokens factory auth token |
| `WEBHOOK_URL` | Yes | URL for CanaryTokens alerts callback |
| `OPENAI_API_KEY` | No | For AI content/image generation |
| `SLACK_WEBHOOK_URL` | No | For Slack alert notifications |
| `SHLINK_API_KEY` | No | For URL shortening via Shlink |
| `SHLINK_DOMAIN` | No | Short URL domain (e.g., `links.example.com`) |

```bash
# Generate secure secrets
openssl rand -hex 32  # Use for DB_PASSWORD, JWT_SECRET_KEY, FACTORY_AUTH
```

### 3. Deploy

```bash
# Start CanaryTokens stack
docker compose -f docker-compose.canarytokens.yml up -d

# Start Campaign Manager
docker compose up -d --build
```

### 4. Access

- **Campaign Manager**: `https://app.yourdomain.com`
- **API**: `https://api.yourdomain.com`
- **CanaryTokens**: `https://tokens.your-canary-domain.com`

## CLI Installation

```bash
cd usb-drop-cli
pip install -e .

# Configure
usb-drop config set-api https://api.yourdomain.com
usb-drop config set-key your-api-key

# Prepare a drive
usb-drop prepare --interactive
```

## Project Structure

```
USB-drop/
├── campaign-api/          # FastAPI backend
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   └── services/      # Business logic
│   └── Dockerfile
├── campaign-frontend/     # Vue 3 frontend
│   ├── src/
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia state
│   │   └── services/      # API client
│   └── Dockerfile
├── usb-drop-cli/          # Python CLI tool
│   └── usb_drop/
├── landing-pages/         # Redirect pages
│   └── rickroll/
├── docs/                  # Documentation
│   ├── DEPLOYMENT.md
│   ├── API.md
│   └── CLI.md
├── docker-compose.yml
├── docker-compose.canarytokens.yml
└── Caddyfile
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Full VPS setup instructions
- [API Reference](docs/API.md) - Complete endpoint documentation
- [CLI Guide](docs/CLI.md) - Command-line tool usage

## Pre-Configured Profiles

The system includes 12 ready-to-use scenario profiles, each with:
- Realistic file structures with multiple token types
- AI-generated images (DALL-E 3) for authenticity
- Suggested USB labels for each scenario

| Category | Profiles |
|----------|----------|
| **Corporate** | IT Department, HR Documents, Finance, Executive, Network Admin |
| **Personal** | Personal/Found Drive, Training/Compliance, Social Creator, Project/Client |
| **Technical** | Developer, Security Audit, Contractor Access |

Each profile automatically includes:
- Word, Excel, and PDF documents with embedded tokens
- Text files with tracking URLs
- QR codes for mobile engagement
- Folder tokens (desktop.ini) for Windows
- AI-generated photos in a Photos folder

## Supported Token Types

| Token Type | File Extension | Trigger Event |
|------------|----------------|---------------|
| **Word Document** | `.docx` | Document opened |
| **Excel Spreadsheet** | `.xlsx` | Spreadsheet opened |
| **PDF Document** | `.pdf` | PDF viewed |
| **DNS Token** | (embedded) | DNS resolution |
| **HTTP URL** | `.txt`, `.url` | Link clicked |
| **QR Code** | `.png` | QR scanned and URL visited |
| **Folder Token** | `desktop.ini` | Folder opened in Windows Explorer |
| **HTML Beacon** | `.html` | HTML file opened in browser |

All tokens are generated via CanaryTokens and trigger real-time alerts with source IP, geolocation, and user agent data.

## Believability Features

Generated USB drives include multiple layers of authenticity to avoid detection as test devices:

### Metadata Injection
| File Type | Injected Metadata |
|-----------|-------------------|
| **Office Documents** | Author, Company, LastModifiedBy, TotalTime (realistic editing duration) |
| **PDF Files** | Author, Producer, Creator (matching application pairs like Word→PDF) |
| **Images** | EXIF data: Camera Make/Model, GPS coordinates, capture settings |

### Timestamp Randomization
File created/modified timestamps are randomized based on scenario type:
- **Corporate** profiles: Business hours (9-5), weekdays only
- **Personal** profiles: Evenings/weekends, varied patterns
- **Technical** profiles: Late night "developer hours"

### Automatic Junk Files
Drives include realistic system artifacts:
- `.DS_Store`, `.Spotlight-V100` (macOS)
- `Thumbs.db` (Windows thumbnail cache)
- `notes.txt`, `_README.txt` (common user files)
- Empty folders like `Documents/Archive/`, `Templates/`

### URL Shortening (Shlink Integration)
When enabled via profile or drive settings, tracking URLs are automatically shortened:
- **Automatic substitution** - All `{canary_token-*}` placeholders use short URLs
- **Unique per link** - Each placeholder in a file gets a unique short URL
- **Configurable slugs** - Base slug + random/sequential suffix (e.g., `docs-a7k2`)
- **Custom domain** - Use your own domain (e.g., `links.company.com`)
- **Believable URLs** - Short URLs appear legitimate, not like tracking links

Configure Shlink in Settings (admin only) or per-profile in the Profile Wizard.

## Workflow Example

1. **Create Campaign** - Set up a new assessment for a client
2. **Select Profile** - Choose from 12 pre-configured scenarios (or create custom)
3. **Prepare Drives** - Generate tokens and create drive packages with AI images
4. **Deploy** - Write files to USB drives, record drop locations
5. **Monitor** - Watch for token triggers in real-time
6. **Report** - Generate campaign summary with maps and statistics

## Security Considerations

- All traffic encrypted via automatic HTTPS (Caddy + Let's Encrypt)
- JWT authentication with short-lived tokens
- API keys for CLI/automation access
- Database isolated in Docker network
- Webhook signature validation

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: user management, settings, all operations |
| **Operator** | Manage campaigns, drives, profiles (no user management) |
| **Viewer** | Read-only access to dashboards and reports |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Disclaimer

This tool is designed for authorized security assessments only. Always obtain proper authorization before conducting USB drop tests. Misuse of this software may violate laws and regulations.
