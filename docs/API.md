# USB Drop Campaign Manager - API Documentation

## Base URL

```
https://api.subproject55.com
```

All endpoints are prefixed with `/api/` (e.g., `/api/auth/login`).

## Authentication

The API supports two authentication methods:

### 1. JWT Token (Web Interface)

```bash
# Login to get tokens
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=yourpassword

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

# Use in requests
Authorization: Bearer <access_token>
```

### 2. API Key (CLI/Automation)

```bash
# Generate API key via web interface or API
POST /api/auth/api-keys
Authorization: Bearer <access_token>

{
  "name": "CLI Tool"
}

# Use in requests
X-API-Key: <api_key>
```

---

## Auth Endpoints

### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=yourpassword
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/x-www-form-urlencoded

refresh_token=eyJ...
```

### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

Response:
```json
{
  "id": "uuid",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Create API Key
```http
POST /api/auth/api-keys

{
  "name": "CLI Tool"
}
```

Response:
```json
{
  "id": "uuid",
  "name": "CLI Tool",
  "key": "udk_abc123...",
  "created_at": "2024-01-15T10:00:00Z"
}
```

Note: The `key` is only returned on creation. Store it securely.

### List API Keys
```http
GET /api/auth/api-keys
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "CLI Tool",
    "created_at": "2024-01-15T10:00:00Z",
    "last_used_at": "2024-01-16T14:30:00Z"
  }
]
```

### Revoke API Key
```http
DELETE /api/auth/api-keys/{key_id}
```

### Change Password
```http
POST /api/auth/change-password

{
  "current_password": "oldpassword",
  "new_password": "newpassword123!"
}
```

Password requirements:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

---

## User Management (Admin Only)

### List Users
```http
GET /api/auth/users
```

Response:
```json
[
  {
    "id": "uuid",
    "username": "operator1",
    "email": "operator@example.com",
    "role": "operator",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### Create User
```http
POST /api/auth/users

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "role": "operator"
}
```

Available roles: `admin`, `operator`, `viewer`

### Get User
```http
GET /api/auth/users/{user_id}
```

### Update User
```http
PUT /api/auth/users/{user_id}

{
  "email": "updated@example.com",
  "role": "viewer",
  "is_active": false
}
```

### Delete User
Deactivates the user account.
```http
DELETE /api/auth/users/{user_id}
```

### Reset User Password
```http
POST /api/auth/users/{user_id}/reset-password

{
  "new_password": "NewSecurePass123!"
}
```

### List Available Roles
```http
GET /api/auth/roles
```

Response:
```json
{
  "roles": [
    {"name": "admin", "description": "Full access to all features"},
    {"name": "operator", "description": "Can manage campaigns and drives"},
    {"name": "viewer", "description": "Read-only access"}
  ]
}
```

---

## Campaigns

### List Campaigns
```http
GET /api/campaigns
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "Q1 2024 Assessment",
    "client_name": "Acme Corp",
    "status": "active",
    "drive_count": 10,
    "triggered_count": 3,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### Create Campaign
```http
POST /api/campaigns

{
  "name": "Q1 2024 Assessment",
  "client_name": "Acme Corp",
  "description": "Quarterly security assessment",
  "landing_page_config": {
    "mode": "included",
    "included_theme": "corporate",
    "delay_seconds": 5
  }
}
```

Landing Page Configuration:
- `mode`: `"disabled"`, `"included"` (built-in theme), or `"custom_url"`
- `included_theme`: Theme name when using included mode
- `custom_url`: Custom landing page URL when using `custom_url` mode
- `delay_seconds`: Redirect delay in seconds (1-30, default: 3)

### List Landing Page Themes
```http
GET /api/campaigns/landing-pages/themes
```

Response:
```json
{
  "themes": [
    {"id": "corporate", "name": "Corporate Portal", "description": "Professional business page"},
    {"id": "login", "name": "Login Page", "description": "Generic login form"},
    {"id": "maintenance", "name": "Maintenance", "description": "Site maintenance notice"},
    {"id": "helpdesk", "name": "IT Helpdesk", "description": "IT support portal"},
    {"id": "hrportal", "name": "HR Portal", "description": "Human resources portal"},
    {"id": "fileshare", "name": "File Share", "description": "File sharing service"},
    {"id": "training", "name": "Training Portal", "description": "Corporate training"},
    {"id": "banking", "name": "Banking", "description": "Financial services"},
    {"id": "document", "name": "Document Viewer", "description": "Document preview"},
    {"id": "survey", "name": "Survey", "description": "Feedback survey"},
    {"id": "onlyfans", "name": "OnlyFans", "description": "Content creator page"}
  ]
}
```

### Get Campaign Details
```http
GET /api/campaigns/{id}
```

### Update Campaign
```http
PUT /api/campaigns/{id}

{
  "name": "Updated Name",
  "status": "completed",
  "landing_page_config": {
    "mode": "included",
    "included_theme": "fileshare",
    "delay_seconds": 10
  }
}
```

### Preview Campaign Deletion
Shows what will be deleted (drives, tokens) before confirming.
```http
GET /api/campaigns/{id}/delete-preview
```

Response:
```json
{
  "campaign": {"id": "uuid", "name": "Q1 Assessment"},
  "drives_count": 10,
  "tokens_count": 45,
  "triggers_count": 12,
  "deployments_count": 8,
  "warning": "This action cannot be undone"
}
```

### Delete Campaign
Deletes campaign and cascades to all drives, tokens, and deployments.
```http
DELETE /api/campaigns/{id}
```

### Get Campaign Statistics
```http
GET /api/campaigns/{id}/stats
```

Response:
```json
{
  "total_drives": 10,
  "deployed": 8,
  "triggered": 3,
  "drives_by_status": {
    "created": 1,
    "prepared": 1,
    "deployed": 5,
    "triggered": 3
  }
}
```

---

## Profiles

### List Profiles
```http
GET /api/profiles
```

### Create Profile
```http
POST /api/profiles

{
  "name": "HR Payroll",
  "description": "HR department payroll documents",
  "scenario_type": "hr",
  "theme": "corporate",
  "token_config": {
    "types": ["dns", "word", "excel"]
  },
  "label_suggestions": ["Payroll Q4", "Benefits 2024"]
}
```

### Get Profile
```http
GET /api/profiles/{id}
```

### Update Profile
```http
PUT /api/profiles/{id}

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Profile
```http
DELETE /api/profiles/{id}
```

### Toggle Profile Active Status
```http
POST /api/profiles/{id}/toggle
```

### Preview Profile
Shows files and tokens that would be generated.
```http
GET /api/profiles/{id}/preview
```

Response:
```json
{
  "files": [
    {"name": "Payroll_Summary.docx", "type": "word"},
    {"name": "Benefits_Overview.xlsx", "type": "excel"}
  ],
  "tokens": ["dns", "word", "excel"],
  "folders": ["Documents", "Photos"]
}
```

### List Profile Templates
```http
GET /api/profiles/templates/list
```

Response:
```json
[
  {
    "id": "it_department",
    "name": "IT Department",
    "category": "corporate",
    "description": "IT support and network files"
  }
]
```

### Get Template Details
```http
GET /api/profiles/templates/{template_id}
```

### Create Profile from Template
```http
POST /api/profiles/from-template/{template_id}

{
  "name": "Custom IT Profile",
  "url_config": {
    "enabled": true,
    "base_slug": "it-docs"
  }
}
```

### List Template Images
```http
GET /api/profiles/template-images/list
```

Response:
```json
{
  "templates": {
    "it_department": {
      "name": "IT Department",
      "images": ["server_room.jpg", "network_diagram.jpg"]
    },
    "social_creator": {
      "name": "Social Creator",
      "images": ["beach_sunset.jpg", "coffee_shop.jpg"]
    }
  }
}
```

### Get Template Image
```http
GET /api/profiles/template-images/{template_id}/{filename}
```

Returns the image file.

### List Text Templates
```http
GET /api/profiles/text-templates/list
```

Response:
```json
[
  {"id": "password_list", "name": "Password List", "description": "Fake credentials file"},
  {"id": "meeting_notes", "name": "Meeting Notes", "description": "Corporate meeting notes"},
  {"id": "project_notes", "name": "Project Notes", "description": "Technical documentation"},
  {"id": "personal_notes", "name": "Personal Notes", "description": "Diary-style notes"},
  {"id": "todo_list", "name": "Todo List", "description": "Task list with URLs"}
]
```

### Get Text Template Content
```http
GET /api/profiles/text-templates/{template_id}
```

### List Token Types
```http
GET /api/profiles/token-types/list
```

Response:
```json
[
  {"id": "dns", "name": "DNS Token", "extension": null},
  {"id": "word", "name": "Word Document", "extension": ".docx"},
  {"id": "excel", "name": "Excel Spreadsheet", "extension": ".xlsx"},
  {"id": "pdf", "name": "PDF Document", "extension": ".pdf"},
  {"id": "url", "name": "HTTP URL", "extension": ".txt"},
  {"id": "qr", "name": "QR Code", "extension": ".png"}
]
```

---

## Profile Files

Manage uploaded files for a profile.

### List Profile Files
```http
GET /api/profiles/{profile_id}/files
```

### Upload File
```http
POST /api/profiles/{profile_id}/files
Content-Type: multipart/form-data

file: <binary>
folder: "Documents"
file_type: "static"
```

File types: `static`, `document`, `template`

### Get File Details
```http
GET /api/profiles/{profile_id}/files/{file_id}
```

### Update File Metadata
```http
PUT /api/profiles/{profile_id}/files/{file_id}

{
  "folder": "Photos",
  "display_name": "vacation.jpg"
}
```

### Download File
```http
GET /api/profiles/{profile_id}/files/{file_id}/download
```

### Delete File
```http
DELETE /api/profiles/{profile_id}/files/{file_id}
```

### Reorder Files
```http
POST /api/profiles/{profile_id}/files/reorder

{
  "file_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Create URL Shortcut
```http
POST /api/profiles/{profile_id}/shortcuts

{
  "filename": "Important Link.url",
  "target_url": "{canary_token-URL}",
  "folder": "Documents",
  "shortcut_type": "url"
}
```

Shortcut types: `url` (Windows), `webloc` (macOS)

### Create Template File
```http
POST /api/profiles/{profile_id}/templates

{
  "filename": "passwords.txt",
  "template_id": "password_list",
  "folder": "Private",
  "custom_content": null
}
```

### Preview Template File
```http
POST /api/profiles/{profile_id}/templates/{file_id}/preview

{
  "token_urls": {
    "{canary_token-URL}": "https://example.com/token123"
  }
}
```

---

## Drives

### List Drives
```http
GET /api/drives?campaign_id={uuid}&status={status}
```

Status values: `created`, `prepared`, `deployed`, `triggered`, `recovered`

### Create Drive
```http
POST /api/drives

{
  "campaign_id": "uuid",
  "profile_id": "uuid",
  "label": "HR Payroll Q4",
  "url_config": {
    "enabled": true,
    "domain": "links.example.com",
    "base_slug": "hr-docs",
    "suffix_mode": "random",
    "suffix_length": 4
  }
}
```

The `url_config` field is optional. If omitted, the drive inherits URL settings from its profile.

Response:
```json
{
  "id": "uuid",
  "unique_code": "USB-A1B2C3",
  "status": "created",
  "label": "HR Payroll Q4"
}
```

### Get Drive by Code
```http
GET /api/drives/by-code/{code}
```

### Get Drive Details
```http
GET /api/drives/{id}
```

### Update Drive
```http
PUT /api/drives/{id}

{
  "label": "Updated Label",
  "notes": "Additional notes"
}
```

### Delete Drive
Deletes drive and all associated tokens from database and CanaryTokens server.
```http
DELETE /api/drives/{id}
```

### Prepare Drive
Creates tokens and generates files.
```http
POST /api/drives/{id}/prepare
```

Response:
```json
{
  "id": "uuid",
  "status": "prepared",
  "tokens": [
    {"id": "uuid", "token_type": "dns", "filename": null},
    {"id": "uuid", "token_type": "word", "filename": "Payroll_Summary.docx"}
  ],
  "files_manifest": {
    "file_count": 12,
    "total_size_bytes": 1048576
  }
}
```

### Download Drive ZIP
```http
GET /api/drives/{id}/download
```

Returns a ZIP file containing all drive files.

### Deploy Drive
Record deployment location.
```http
POST /api/drives/{id}/deploy

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_description": "Building A lobby",
  "deployed_by": "John Smith"
}
```

### Deploy with Photo
Record deployment with photo (extracts GPS from EXIF).
```http
POST /api/drives/{id}/deploy-with-photo
Content-Type: multipart/form-data

photo: <binary>
location_description: "Near reception"
deployed_by: "John Smith"
```

### Get Drive Tokens
```http
GET /api/drives/{id}/tokens
```

### Get Drive Deployment
```http
GET /api/drives/{id}/deployment
```

Response:
```json
{
  "id": "uuid",
  "drive_id": "uuid",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_name": "Building A",
  "location_description": "Main lobby entrance",
  "location_type": "office_building",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "country": "US",
  "photo_url": "/uploads/deployments/photo.jpg",
  "deployed_by": "John Smith",
  "deployment_notes": "Left near reception desk",
  "deployed_at": "2024-01-15T10:00:00Z"
}
```

### Update Drive Deployment
```http
PUT /api/drives/{id}/deployment

{
  "location_description": "Updated location",
  "deployment_notes": "Added more details"
}
```

---

## Tokens

### Get Token Details
```http
GET /api/tokens/{token_id}
```

Response:
```json
{
  "id": "uuid",
  "drive_id": "uuid",
  "token_type": "word",
  "filename": "Payroll_Summary.docx",
  "canary_token_id": "abc123",
  "token_url": "https://tokens.example.com/abc123",
  "created_at": "2024-01-15T10:00:00Z",
  "trigger_count": 5
}
```

### Get Token Triggers
```http
GET /api/tokens/{token_id}/triggers
```

Response:
```json
[
  {
    "id": "uuid",
    "source_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "geo_city": "San Francisco",
    "geo_country": "US",
    "triggered_at": "2024-01-15T14:30:00Z"
  }
]
```

### Delete Token
Deletes token from database and CanaryTokens server.
```http
DELETE /api/tokens/{token_id}
```

---

## Short URLs

Manage shortened URLs for tokens.

### Create Short URL
```http
POST /api/shortener/drives/{drive_id}/tokens/{token_id}

{
  "custom_slug": "hr-docs-2024"
}
```

Response:
```json
{
  "id": "uuid",
  "short_url": "https://links.example.com/hr-docs-2024",
  "target_url": "https://tokens.example.com/abc123",
  "slug": "hr-docs-2024",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### List Drive Short URLs
```http
GET /api/shortener/drives/{drive_id}
```

### Get Short URL Details
```http
GET /api/shortener/{short_url_id}
```

### Get Short URL Stats
```http
GET /api/shortener/{short_url_id}/stats
```

Response:
```json
{
  "id": "uuid",
  "short_url": "https://links.example.com/hr-docs-2024",
  "visit_count": 42,
  "visits_by_day": {
    "2024-01-15": 10,
    "2024-01-16": 32
  }
}
```

### Delete Short URL
```http
DELETE /api/shortener/{short_url_id}
```

### Bulk Create Short URLs
```http
POST /api/shortener/bulk/drives/{drive_id}

{
  "token_ids": ["uuid1", "uuid2", "uuid3"],
  "base_slug": "hr-docs",
  "suffix_mode": "random"
}
```

---

## Targets (Organizations)

Manage target organization profiles for campaigns.

### Get Field Options
```http
GET /api/targets/options
```

Response:
```json
{
  "industries": ["technology", "finance", "healthcare", "manufacturing", "retail", "other"],
  "company_sizes": ["startup", "smb", "mid_market", "enterprise", "global"],
  "departments": ["it", "hr", "finance", "executive", "engineering", "sales", "marketing"],
  "regions": ["us_east", "us_west", "europe", "asia_pacific", "latam"]
}
```

### List Targets
```http
GET /api/targets?industry={industry}
```

### Create Target
```http
POST /api/targets

{
  "name": "Acme Corp Assessment",
  "company_name": "Acme Corporation",
  "industry": "technology",
  "company_size": "enterprise",
  "target_department": "engineering",
  "geographic_region": "us_west",
  "known_technologies": ["AWS", "Kubernetes", "Python"],
  "email_domain": "acme.com",
  "website": "https://acme.com",
  "osint_notes": "Uses Slack for internal comms"
}
```

### Get Target
```http
GET /api/targets/{target_id}
```

### Update Target
```http
PUT /api/targets/{target_id}

{
  "osint_notes": "Updated reconnaissance notes"
}
```

### Delete Target
```http
DELETE /api/targets/{target_id}
```

### Get Scenario Recommendation
Uses AI to recommend the best profile scenario for the target.
```http
POST /api/targets/{target_id}/recommend-scenario
```

Response:
```json
{
  "recommended_profile": "it_department",
  "confidence": "high",
  "reasoning": "Target is a tech company with engineering focus...",
  "alternative_profiles": ["developer", "network_admin"],
  "suggested_labels": ["IT Tools Q4", "DevOps Resources"],
  "suggested_filenames": ["kubernetes_config.docx", "aws_credentials.xlsx"],
  "risk_factors": ["Tech-savvy employees may be suspicious"],
  "tips": ["Use technical jargon in filenames"]
}
```

---

## Alerts

### List Recent Alerts
```http
GET /api/alerts/recent?hours=24
```

Response:
```json
[
  {
    "id": "uuid",
    "drive_code": "USB-A1B2C3",
    "token_type": "word",
    "token_filename": "Payroll_Summary.docx",
    "source_ip": "192.168.1.100",
    "geo_city": "San Francisco",
    "geo_country": "US",
    "triggered_at": "2024-01-15T14:30:00Z"
  }
]
```

### Get Alert Statistics
```http
GET /api/alerts/stats?campaign_id={uuid}
```

Response:
```json
{
  "total": 150,
  "today": 5,
  "this_week": 23,
  "unique_ips": 45
}
```

### Get Map Data
```http
GET /api/alerts/map?campaign_id={uuid}
```

Response:
```json
[
  {
    "id": "uuid",
    "type": "deployment",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "label": "Dropped: USB-A1B2",
    "drive_code": "USB-A1B2",
    "timestamp": "2024-01-15T10:00:00Z",
    "details": {
      "location_name": "Building A",
      "location_type": "office_building"
    }
  },
  {
    "id": "uuid",
    "type": "trigger",
    "latitude": 37.7849,
    "longitude": -122.4094,
    "label": "Triggered: USB-A1B2",
    "drive_code": "USB-A1B2",
    "timestamp": "2024-01-15T14:30:00Z",
    "details": {
      "token_type": "word",
      "filename": "Payroll_Summary.docx",
      "source_ip": "192.168.1.100"
    }
  }
]
```

---

## Content Generation

### Generate Document
```http
POST /api/generate/document

{
  "document_type": "memo",
  "topic": "Q4 payroll adjustments",
  "tone": "professional",
  "length": "medium"
}
```

Response:
```json
{
  "content": "MEMORANDUM\n\nTo: All Employees...",
  "filename": "memo_payroll_adjustments.docx"
}
```

### Generate Image
```http
POST /api/generate/image

{
  "prompt": "Professional corporate office building",
  "style": "photorealistic",
  "size": "1024x1024"
}
```

---

## Reports

### Get Campaign Report
```http
GET /api/reports/campaign/{id}
```

Response:
```json
{
  "campaign": {
    "id": "uuid",
    "name": "Q1 Assessment",
    "client_name": "Acme Corp"
  },
  "total_drives": 10,
  "deployed": 8,
  "triggered": 3,
  "total_triggers": 15,
  "status_distribution": {
    "created": 1,
    "prepared": 1,
    "deployed": 5,
    "triggered": 3
  },
  "triggers_by_day": {
    "2024-01-15": 5,
    "2024-01-16": 10
  },
  "triggers_by_type": {
    "dns": 3,
    "word": 8,
    "excel": 4
  },
  "top_drives": [
    {
      "id": "uuid",
      "unique_code": "USB-A1B2",
      "trigger_count": 5,
      "first_trigger": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### Export Campaign CSV
```http
GET /api/reports/export/{id}/csv
```

Returns a CSV file with all campaign data.

---

## Webhooks

### CanaryTokens Webhook
Receives trigger notifications from CanaryTokens.
```http
POST /api/webhooks/canary

{
  "token": "canary-token-id",
  "src_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "additional_data": {}
}
```

---

## Settings (Admin Only)

### Get Shlink Status
```http
GET /api/settings/shlink/status
```

Response:
```json
{
  "connected": true,
  "domain": "links.subproject55.com",
  "api_url": "http://shlink:8080",
  "short_url_count": 42,
  "error": null
}
```

### Get Shlink Configuration
```http
GET /api/settings/shlink/config
```

### Test Shlink Connection
```http
POST /api/settings/shlink/test
```

Response:
```json
{
  "success": true,
  "test_url": "https://example.com/test",
  "short_url": "https://links.example.com/abc123",
  "error": null
}
```

### Get All Profile URL Configurations
```http
GET /api/settings/url-configs
```

### Update Profile URL Configuration
```http
PUT /api/settings/url-configs/{profile_id}

{
  "enabled": true,
  "base_slug": "hr-docs",
  "suffix_mode": "random",
  "suffix_length": 4
}
```

Suffix modes:
- `random` - Random alphanumeric suffix
- `drive_code` - Uses drive code
- `sequential` - Sequential numbering

### Bulk Update URL Configurations
```http
PUT /api/settings/url-configs/bulk

[
  {
    "id": "profile-uuid",
    "enabled": true,
    "base_slug": "hr-docs"
  }
]
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

Validation errors include field details:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid auth)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

API requests are limited to:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated endpoints

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705329600
```
