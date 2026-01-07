# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **USB drop penetration testing campaign management system** using CanaryTokens. It provides a complete workflow for authorized security assessments.

**Important**: All materials are for authorized penetration testing with explicit written permission. USB drop testing requires documented ROE, scope definitions, and legal approval.

## Architecture

```
├── campaign-api/          # FastAPI backend (Python 3.9+)
├── campaign-frontend/     # Vue 3 + Vite + Tailwind frontend
├── usb-drop-cli/         # Click-based CLI tool
├── landing-pages/        # Flask landing pages (rickroll)
├── docker-compose.yml    # Main deployment (Caddy, API, Frontend, Postgres)
└── docker-compose.canarytokens.yml  # CanaryTokens stack
```

### Campaign API (FastAPI)

- **Entry**: `campaign-api/app/main.py`
- **Routers**: `app/routers/` - auth, campaigns, profiles, drives, tokens, webhooks, alerts, generate, reports
- **Models**: `app/models/` - SQLAlchemy ORM (User, Campaign, Profile, ProfileFile, Drive, Token, ShortUrl, Deployment, Trigger, Content)
- **Services**: `app/services/` - canary_client.py (CanaryTokens API), usb_builder.py, content_generator.py (OpenAI), slack_notifier.py, geo_service.py, and believability services (see below)
- **Database**: PostgreSQL via SQLAlchemy, auto-creates tables on startup

### Campaign Frontend (Vue 3)

- **Entry**: `campaign-frontend/src/main.js`
- **Router**: `src/router/index.js`
- **State**: Pinia stores in `src/stores/`:
  - `auth.js` - Authentication and user state
  - `profileWizard.js` - Profile creation/editing wizard state
- **Views**: Dashboard, Campaigns, Profiles, Drives, DriveDetail, CampaignDetail, MapView (Leaflet), Alerts, Reports
- **Wizard Components** (`src/components/wizard/`):
  - `ScenarioStep.vue` - Profile type selection
  - `FolderStep.vue` - Folder structure configuration
  - `TokenStep.vue` - File/token configuration with content editor
  - `ContentStep.vue` - URL shortener and additional settings
  - `ReviewStep.vue` - Final review before save
  - `TemplateEditor.vue` - Rich text editor with placeholder support

### USB Drop CLI

- **Entry**: `usb-drop-cli/usb_drop/cli.py`
- **Install**: `cd usb-drop-cli && pip install -e .`
- **Command**: `usb-drop`

## VPS Deployment

**SSH Access:**
```bash
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119
```

**Project Location:** `/opt/usb-drop/`

**Deploy Individual Files:**
```bash
# Deploy a single API file
scp -i ~/.ssh/claude_deploy campaign-api/app/services/usb_builder.py deploy@74.208.78.119:/opt/usb-drop/campaign-api/app/services/

# Deploy a single frontend file
scp -i ~/.ssh/claude_deploy campaign-frontend/src/views/Drives.vue deploy@74.208.78.119:/opt/usb-drop/campaign-frontend/src/views/
```

**Sync & Deploy (bulk):**
```bash
# Sync API changes
rsync -avz --delete -e "ssh -i ~/.ssh/claude_deploy" campaign-api/app/ deploy@74.208.78.119:/opt/usb-drop/campaign-api/app/

# Sync frontend changes
rsync -avz --delete -e "ssh -i ~/.ssh/claude_deploy" campaign-frontend/src/ deploy@74.208.78.119:/opt/usb-drop/campaign-frontend/src/

# Rebuild containers on VPS
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "cd /opt/usb-drop && docker compose up -d --build api campaign-frontend"
```

**Container Management:**
```bash
# Check container status
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "docker ps"

# View API logs
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "docker logs usb-drop-api-1 --tail 50"

# Restart a container
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "cd /opt/usb-drop && docker compose restart api"
```

**Database Queries (Debugging):**
```bash
# Query drive manifest by unique code
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "docker exec usb-drop-postgres-1 psql -U usbdrop -d usbdrop -c \"SELECT files_manifest FROM drives WHERE unique_code = 'USB-XXXXXX';\""

# List recent drives
ssh -i ~/.ssh/claude_deploy deploy@74.208.78.119 "docker exec usb-drop-postgres-1 psql -U usbdrop -d usbdrop -c \"SELECT unique_code, status, created_at FROM drives ORDER BY created_at DESC LIMIT 10;\""
```

## Development Commands

### Docker (Full Stack)

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f api
docker compose logs -f campaign-frontend

# Start CanaryTokens separately
docker compose -f docker-compose.canarytokens.yml up -d
```

### API Development

```bash
cd campaign-api

# Install dependencies
pip install -r requirements.txt

# Run locally (requires Postgres)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head
```

### Frontend Development

```bash
cd campaign-frontend

# Install dependencies
npm install

# Development server (port 5173)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### CLI Development

```bash
cd usb-drop-cli

# Install in development mode
pip install -e .

# Configure
usb-drop config set-api https://api.example.com
usb-drop config set-key <api-key>

# Example commands
usb-drop list-campaigns
usb-drop prepare --interactive
usb-drop download <drive-id> --usb
```

## Key Technical Details

### Authentication

- JWT tokens for web UI (access + refresh tokens)
- API keys for CLI/automation (`X-API-Key` header)
- Initial admin created from `ADMIN_*` env vars on first startup

### User Management & Roles

Role-based access control with three permission levels:

| Role | Permissions |
|------|-------------|
| **admin** | Full access: user management, all operations |
| **operator** | Can manage campaigns, drives, profiles (no user management) |
| **viewer** | Read-only access to dashboards and reports |

**API Endpoints** (`/api/auth/`):
- `GET /users` - List all users (admin only)
- `POST /users` - Create user (admin only)
- `PUT /users/{id}` - Update user role/status (admin only)
- `DELETE /users/{id}` - Deactivate user (admin only)
- `POST /users/{id}/reset-password` - Reset password (admin only)
- `POST /change-password` - Change own password (any user)
- `GET /roles` - List available roles

**Password Requirements**:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Key Files**:
- `app/models/user.py` - User model with UserRole enum
- `app/routers/auth.py` - Auth endpoints including user management
- `campaign-frontend/src/views/Users.vue` - User management UI (admin only)
- `campaign-frontend/src/stores/auth.js` - Auth store with role checks

### CanaryTokens Integration

The API proxies to a self-hosted CanaryTokens instance:
```
CANARY_SERVER=http://canarytokens-frontend:8082
FACTORY_AUTH=<token>
```

Token creation via `canary_client.py` calls CanaryTokens factory API.

### Drive Management

**API Endpoints** (`/api/drives/`):
- `GET /` - List drives (with optional `campaign_id` and `status` filters)
- `POST /` - Create a new drive
- `GET /{id}` - Get drive details
- `PUT /{id}` - Update drive
- `DELETE /{id}` - Delete drive and all associated tokens (from DB and CanaryTokens)
- `POST /{id}/prepare` - Generate tokens and prepare files for the drive
- `GET /{id}/download` - Download drive contents as ZIP
- `POST /{id}/deploy` - Record deployment location
- `POST /{id}/deploy-with-photo` - Record deployment with photo (extracts GPS from EXIF)
- `GET /{id}/tokens` - List tokens for a drive
- `GET /{id}/deployment` - Get deployment details

**Drive Lifecycle:**
1. `created` - Drive record exists, no tokens yet
2. `prepared` - Tokens generated, ready for download
3. `deployed` - Physically placed in the field
4. `triggered` - At least one token has been accessed
5. `recovered` - Drive was collected

### Campaign Management

**API Endpoints** (`/api/campaigns/`):
- `DELETE /{id}` - Delete campaign and cascade to all drives/tokens

Deletion cascades properly: Campaign → Drives → Tokens/Deployments

### Profile System

- **12 pre-configured profiles** are seeded on API startup via `profile_seeder.py`
- Templates defined in `content_templates.py` with PROFILE_TEMPLATES dict
- Each profile includes AI-generated images stored in `/app/uploads/template_images/{template_id}/`
- Profiles organized into categories: Corporate, Personal/Social, Technical
- Files include: Word/Excel/PDF tokens, text files with URLs, QR codes, folder tokens, template images

**Profile Wizard** (`campaign-frontend/src/stores/profileWizard.js`):
- 5-step wizard: Scenario → Folders → Files/Tokens → Content → Review
- Supports custom content with token placeholders
- File upload support for custom documents
- URL shortener configuration per profile

**Token Placeholder System**:

Files can include placeholders that get replaced when the drive is prepared:

| Placeholder | Description |
|-------------|-------------|
| `{canary_token-URL}` | HTTP URL token (triggers on access) |
| `{canary_token-DNS}` | DNS token (triggers on resolution) |
| `{canary_token-WORD}` | MS Word document token |
| `{canary_token-EXCEL}` | MS Excel document token |
| `{canary_token-PDF}` | PDF document token |
| `{canary_token-QR}` | QR code image token |
| `{short_url}` | Shortened URL (explicit, for backwards compatibility) |
| `{drive_code}` | Drive unique code (e.g., USB-A1B2C3) |

**Automatic Short URL Substitution**: When URL shortening is enabled on a drive, all `{canary_token-*}` placeholders automatically use the shortened URL instead of the raw canary token URL. No need to use `{short_url}` explicitly.

**Text File Templates**:

Text files use templates from `content_generator.py`. Available templates:
- `password_list` (default) - Fake credentials with embedded token URLs
- `meeting_notes` - Corporate meeting notes with shared links
- `project_notes` - Technical project documentation
- `personal_notes` - Personal diary-style notes
- `todo_list` - Task list with reference URLs

When no template is specified, files automatically use `password_list`.

**Custom Content**:

Files can have custom content with placeholders:
- Set via `custom_content` field in file definition
- Placeholders are replaced at prepare time
- Supports `.txt`, `.docx`, `.pdf` output formats
- Custom content files are converted to `.txt` for simplicity

**URL Shortener**:

Profiles can configure URL shortening for token URLs:
- `enabled` - Enable/disable URL shortening
- `base_slug` - Base path for short URLs (e.g., "docs")
- `suffix_mode` - `random` or `sequential` suffix generation
- `suffix_length` - Length of random suffix (default: 4)
- `domain` - Custom domain for short URLs

**Profile Files API** (`/api/profiles/{id}/files/`):
- `GET /` - List uploaded files for a profile
- `POST /` - Upload a file to a profile
- `GET /{file_id}` - Get file details
- `PUT /{file_id}` - Update file metadata
- `DELETE /{file_id}` - Delete uploaded file

Uploaded files are stored in `/app/uploads/profile_files/{profile_id}/`

### Drive Files Manifest

When a drive is prepared, `usb_builder.py` creates a `files_manifest` JSON stored in the database. This manifest is used by `create_zip()` to generate the downloadable ZIP file.

**Manifest Structure:**
```json
{
  "folders": ["pics", "priv"],
  "files": [...],
  "file_count": 7,
  "total_size_bytes": 28642,
  "prepared_at": "2026-01-07T02:09:04.528577"
}
```

**File Types in Manifest:**

| `file_type` | Description | Key Fields |
|-------------|-------------|------------|
| *(empty)* | Standard token files (Word, Excel, PDF, text) | `token_id`, `auth_token`, `token_type`, `token_url` |
| `custom_content` | Text files with custom content and placeholders | `custom_content`, `token_urls` (dict of placeholder→URL) |
| `template` | Uploaded template files with placeholders | `custom_content`, `token_urls`, `profile_file_id` |
| `document` | Uploaded documents with injected tokens | `stored_filename`, `profile_file_id`, `token_url`, `mime_type` |
| `static` | Static files (images) copied as-is | `stored_filename`, `profile_file_id` |
| `shortcut` | URL shortcut files (.url, .webloc) | `target_url`, `shortcut_type` |

**Important:** Files with a `file_type` field are processed differently than standard token files. The `create_zip()` function checks for `file_type` to determine how to generate file content:
- Standard files: Download from CanaryTokens using `token_id`
- `custom_content`/`template`: Replace placeholders in `custom_content` string
- `shortcut`: Regenerate from `target_url` (content not stored in manifest)
- `document`/`static`: Read from profile file storage

### Believability Services

Services that make generated USB drive contents appear authentic:

| Service | File | Purpose |
|---------|------|---------|
| **Timestamp Service** | `timestamp_service.py` | Randomizes file timestamps (created/modified) based on scenario type |
| **EXIF Service** | `exif_service.py` | Injects realistic camera metadata (Make, Model, GPS, settings) into images |
| **Office Metadata** | `office_metadata_service.py` | Adds Author, Company, LastModifiedBy, TotalTime to Word/Excel docs |
| **PDF Metadata** | `pdf_metadata_service.py` | Injects Author, Producer, Creator with realistic application pairs |
| **URL Generator** | `url_generator.py` | Creates believable URLs mimicking SharePoint, OneDrive, Google Drive, etc. |
| **Folder Templates** | `folder_templates.py` | Adds scenario-appropriate junk files (.DS_Store, Thumbs.db, notes.txt) |

These services are automatically invoked by `usb_builder.py` when creating drive ZIPs.

**Automatic Junk Files**:

Drives automatically include realistic junk files based on scenario type:
- `.DS_Store`, `.Spotlight-V100` (macOS artifacts)
- `Thumbs.db` (Windows thumbnail cache)
- `notes.txt`, `_README.txt` (common user files)
- `Documents/Archive/`, `Meeting_Notes/`, `Templates/` (common folders)

These files make the USB drive appear to be a real user's device rather than a prepared test drive.

### Environment Variables

See `.env.example` for all required variables:
- `DB_PASSWORD`, `JWT_SECRET_KEY`, `FACTORY_AUTH` - generate with `openssl rand -hex 32`
- `CANARY_DOMAIN` - domain for CanaryTokens
- `WEBHOOK_URL` - URL for CanaryTokens alerts callback (required for token creation)
- `OPENAI_API_KEY` - for content generation
- `SLACK_WEBHOOK_URL` - for alert notifications

### API Keys

The `secrets/` folder (not in repo) contains API key documentation for:
- **Google API** - Maps/GeoIP features, Docs tokens
- **Mailgun** - Email notifications
- **IPinfo** - IP geolocation lookups

## Content Guidelines

- All scenarios assume proper authorization
- CanaryTokens are detection tripwires, not malware
- Do not create or improve malicious payloads
- Analysis, documentation, and defensive guidance are appropriate
