# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a security research and **full-stack application** repository for authorized USB drop penetration testing campaigns using CanaryTokens. It includes a Campaign Manager web application, REST API, CLI tool, and research documentation.

**Important**: All materials are intended for authorized penetration testing engagements with explicit written permission.

## Architecture

```
                    Internet
                        |
                    [Caddy]  (automatic HTTPS)
                   /   |   \
                  /    |    \
        [Frontend] [API] [CanaryTokens]
         (Vue 3)  (FastAPI)    |
                     |      [Redis]
                [PostgreSQL]

Docker Networks:
- frontend: Caddy ↔ API ↔ Frontend ↔ Landing pages
- backend:  API ↔ PostgreSQL (isolated)
- canarytokens: API ↔ CanaryTokens ↔ Redis
```

### Components

| Component | Location | Stack |
|-----------|----------|-------|
| Campaign API | `project-files/campaign-api/` | FastAPI, SQLAlchemy, Pydantic |
| Frontend | `project-files/campaign-frontend/` | Vue 3, Vite, Tailwind, Pinia |
| CLI Tool | `project-files/usb-drop-cli/` | Python, Click, Rich |
| Landing Pages | `project-files/landing-pages/` | Flask |
| Docker Config | `project-files/` | Caddy, PostgreSQL, Redis |

## Development Commands

### API (FastAPI)

```bash
cd project-files/campaign-api

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend (Vue 3)

```bash
cd project-files/campaign-frontend

# Install dependencies
npm install

# Development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### CLI Tool

```bash
cd project-files/usb-drop-cli

# Install in development mode
pip install -e .

# Run commands
usb-drop --help
usb-drop list-campaigns
usb-drop prepare --interactive
```

### Docker Deployment

```bash
cd project-files

# Copy and configure environment
cp .env.example .env

# Start all services
docker compose up -d --build

# View logs
docker compose logs -f api
docker compose logs -f campaign-frontend

# Start CanaryTokens separately
docker compose -f docker-compose.canarytokens.yml up -d

# Database backup
docker compose exec postgres pg_dump -U usbdrop usbdrop > backup.sql
```

### Remote Server Access

```bash
# SSH to production VPS (my-vps)
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119
```

## API Structure

**Base Path**: `/api`

| Router | Prefix | Description |
|--------|--------|-------------|
| auth | `/api/auth` | JWT/API key authentication |
| campaigns | `/api/campaigns` | Campaign CRUD, statistics |
| profiles | `/api/profiles` | USB payload profile templates |
| drives | `/api/drives` | Individual USB drive management |
| tokens | `/api/tokens` | CanaryToken lifecycle |
| webhooks | `/api/webhooks` | CanaryTokens trigger receiver |
| alerts | `/api/alerts` | Trigger alerts and map data |
| generate | `/api/generate` | AI content generation (OpenAI) |
| reports | `/api/reports` | Campaign reporting/export |

## Data Models

Core entities in `project-files/campaign-api/app/models/`:

- **User/APIKey** - Authentication
- **Campaign** - Top-level engagement container
- **Profile** - Reusable USB payload templates
- **Drive** - Individual USB with unique code (e.g., `USB-A1B2-ACME`)
- **Token** - CanaryToken instances linked to drives
- **Deployment** - Physical drop location records
- **Trigger** - Token activation events with geolocation

## Key Services

- `canary_client.py` - CanaryTokens API wrapper (`factory.create`, `factory.download`, etc.)
- `usb_builder.py` - USB file structure generation
- `content_generator.py` - OpenAI-powered document generation
- `slack_notifier.py` - Alert notifications
- `geo_service.py` - IP geolocation for triggers

## CanaryTokens Integration

The API integrates with a self-hosted CanaryTokens instance:

```python
# Token creation via CanaryTokensClient
client = CanaryTokensClient()
token = await client.create_token(
    kind="doc-msword",  # dns, doc-msexcel, pdf-acrobat-reader, windows-dir, etc.
    memo="USB-A1B2-ACME:word",
    email="alerts@example.com"
)
```

Webhook endpoint `/api/webhooks/canary` receives trigger notifications and records them as `Trigger` events.

## Environment Variables

Key variables (see `project-files/.env.example`):

- `DATABASE_URL` - PostgreSQL connection
- `FACTORY_AUTH` - CanaryTokens API authentication
- `CANARY_DOMAIN` - Self-hosted CanaryTokens domain
- `JWT_SECRET_KEY` - API authentication
- `OPENAI_API_KEY` - Content generation (optional)
- `SLACK_WEBHOOK_URL` - Alert notifications (optional)

## Frontend State Management

The Vue 3 frontend uses Pinia for state management. The primary store is `src/stores/auth.js` which handles JWT authentication state. Views are located in `src/views/` and correspond to main application routes (Dashboard, Campaigns, Drives, MapView, Alerts, Reports).

## Content Guidelines

When working with this content:
- Do not create actual malicious payloads
- Do not improve or augment attack code
- Analysis, documentation, and defensive guidance are appropriate
- Treat scenario templates as pentesting engagement documentation
