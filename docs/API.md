# USB Drop Campaign Manager - API Documentation

## Base URL

```
https://api.subproject55.com
```

## Authentication

The API supports two authentication methods:

### 1. JWT Token (Web Interface)

```bash
# Login to get tokens
POST /auth/login
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
POST /auth/api-keys
Authorization: Bearer <access_token>

{
  "name": "CLI Tool"
}

# Use in requests
X-API-Key: <api_key>
```

## Endpoints

### Campaigns

#### List Campaigns
```http
GET /campaigns
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

#### Create Campaign
```http
POST /campaigns

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
- `mode`: `"disabled"` (use profile settings), `"included"` (use built-in theme), or `"custom_url"`
- `included_theme`: Theme name when using included mode. Available themes: `corporate`, `login`, `maintenance`, `helpdesk`, `hrportal`, `fileshare`, `training`, `banking`, `document`, `survey`, `onlyfans`
- `custom_url`: Custom landing page URL when using `custom_url` mode
- `delay_seconds`: Redirect delay in seconds (1-30, default: 3)

#### Get Campaign Details
```http
GET /campaigns/{id}
```

#### Update Campaign
```http
PUT /campaigns/{id}

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

See [Create Campaign](#create-campaign) for `landing_page_config` options.

#### Get Campaign Statistics
```http
GET /campaigns/{id}/stats
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

### Profiles

#### List Profiles
```http
GET /profiles
```

#### Create Profile
```http
POST /profiles

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

#### Preview Profile
```http
GET /profiles/{id}/preview
```

Response:
```json
{
  "files": [
    {"name": "Payroll_Summary.docx", "type": "word"},
    {"name": "Benefits_Overview.xlsx", "type": "excel"}
  ],
  "tokens": ["dns", "word", "excel"]
}
```

#### List Template Images
```http
GET /profiles/template-images/list
```

Response:
```json
{
  "templates": {
    "it_department": {
      "name": "IT Department",
      "images": ["server_room.jpg", "network_diagram.jpg", "helpdesk_workspace.jpg"]
    },
    "social_creator": {
      "name": "Social Creator",
      "images": ["beach_sunset.jpg", "coffee_shop.jpg", "mirror_selfie.jpg", "rooftop_city.jpg"]
    }
  }
}
```

#### Get Template Image
```http
GET /profiles/template-images/{template_id}/{filename}
```

Returns the AI-generated image file for a specific template.

---

### Drives

#### List Drives
```http
GET /drives?campaign_id={uuid}&status={status}
```

#### Create Drive
```http
POST /drives

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

The `url_config` field is optional. If omitted, the drive inherits URL settings from its profile. If provided, it overrides the profile's URL configuration for this drive only.

Response:
```json
{
  "id": "uuid",
  "unique_code": "USB-A1B2-ACME",
  "status": "created",
  "label": "HR Payroll Q4"
}
```

#### Prepare Drive
Creates tokens and generates files.
```http
POST /drives/{id}/prepare
```

Response:
```json
{
  "id": "uuid",
  "status": "prepared",
  "tokens": [
    {"id": "uuid", "token_type": "dns", "filename": null},
    {"id": "uuid", "token_type": "word", "filename": "Payroll_Summary.docx"}
  ]
}
```

#### Download Drive ZIP
```http
GET /drives/{id}/download
```

Returns a ZIP file containing all drive files including:
- Token-embedded documents (Word, Excel, PDF)
- Text files with tracking URLs
- QR code images
- AI-generated template images (Photos folder)
- Folder tokens (desktop.ini files)

**URL Shortening**: When URL shortening is enabled (via profile or drive `url_config`), each `{canary_url}` placeholder in text files receives a unique short URL. For example, a text file with 6 URL placeholders will have 6 different short URLs like:
```
Subscribe: https://links.example.com/hr-docs-mmoe
Exclusive Content: https://links.example.com/hr-docs-2xh9
Management: https://links.example.com/hr-docs-3nqk
```
All URLs redirect to the same canary token but appear unique for believability.

#### Deploy Drive
Record deployment location.
```http
POST /drives/{id}/deploy

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_description": "Building A lobby",
  "deployed_by": "John Smith"
}
```

#### Get Drive by Code
```http
GET /drives/by-code/{code}
```

#### Get Drive Tokens
```http
GET /drives/{id}/tokens
```

#### Get Drive Deployment
```http
GET /drives/{id}/deployment
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
  "deployed_at": "2024-01-15T10:00:00Z",
  "photo_taken_at": "2024-01-15T09:55:00Z"
}
```

#### Update Drive Deployment
Update deployment details for a deployed or triggered drive.
```http
PUT /drives/{id}/deployment

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_name": "Building A - Updated",
  "location_description": "Near elevator bank",
  "location_type": "office_building",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "country": "US",
  "deployed_by": "John Smith",
  "deployment_notes": "Updated location after finding actual drop spot"
}
```

Note: This endpoint allows editing deployment details even after a drive has been triggered, useful for correcting location information or adding notes based on trigger data.

---

### Alerts

#### List Recent Alerts
```http
GET /alerts/recent?hours=24
```

Response:
```json
[
  {
    "id": "uuid",
    "drive_code": "USB-A1B2-ACME",
    "token_type": "word",
    "token_filename": "Payroll_Summary.docx",
    "source_ip": "192.168.1.100",
    "geo_city": "San Francisco",
    "geo_country": "US",
    "triggered_at": "2024-01-15T14:30:00Z"
  }
]
```

#### Get Alert Statistics
```http
GET /alerts/stats?campaign_id={uuid}
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

#### Get Map Data
```http
GET /alerts/map?campaign_id={uuid}
GET /alerts/mapdata?campaign_id={uuid}  # Alias endpoint
```

Returns an array of map points for visualization. Each point has a `type` field indicating whether it's a deployment or trigger event.

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
      "source_ip": "192.168.1.100",
      "geo_city": "San Francisco",
      "geo_country": "US"
    }
  }
]
```

Map Point Fields:
- `type`: Either `"deployment"` or `"trigger"`
- `latitude`/`longitude`: Geographic coordinates
- `label`: Display label for map markers
- `drive_code`: Associated drive identifier
- `timestamp`: When the event occurred
- `details`: Additional context (varies by type)

---

### Content Generation

#### Generate Document
```http
POST /generate/document

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
  "content": "MEMORANDUM\n\nTo: All Employees\nFrom: HR Department...",
  "filename": "memo_payroll_adjustments.docx"
}
```

#### Generate Image
```http
POST /generate/image

{
  "prompt": "Professional corporate office building",
  "style": "photorealistic",
  "size": "1024x1024"
}
```

---

### Reports

#### Get Campaign Report
```http
GET /reports/campaign/{id}
```

Response:
```json
{
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

#### Export Campaign CSV
```http
GET /reports/export/{id}/csv
```

Returns a CSV file with all campaign data.

---

### Webhooks

#### CanaryTokens Webhook
Receives trigger notifications from CanaryTokens.
```http
POST /webhooks/canary

{
  "token": "canary-token-id",
  "src_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "additional_data": {}
}
```

---

### Settings (Admin Only)

#### Get Shlink Status
Check connection status of the Shlink URL shortener.
```http
GET /settings/shlink/status
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

#### Get Shlink Configuration
```http
GET /settings/shlink/config
```

Response:
```json
{
  "domain": "links.subproject55.com",
  "api_url": "http://shlink:8080",
  "configured": true
}
```

#### Test Shlink Connection
Creates and immediately deletes a test short URL to verify connectivity.
```http
POST /settings/shlink/test
```

Response:
```json
{
  "success": true,
  "test_url": "https://example.com/shlink-connection-test",
  "short_url": "https://links.subproject55.com/abc123",
  "error": null
}
```

#### Get All Profile URL Configurations
```http
GET /settings/url-configs
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "HR Documents",
    "scenario_type": "hr_documents",
    "enabled": true,
    "url_config": {
      "enabled": true,
      "base_slug": "hr-docs",
      "suffix_mode": "random",
      "suffix_length": 4
    }
  }
]
```

#### Update Profile URL Configuration
```http
PUT /settings/url-configs/{profile_id}

{
  "enabled": true,
  "base_slug": "hr-docs",
  "suffix_mode": "random",
  "suffix_length": 4
}
```

Suffix modes:
- `random` - Random alphanumeric suffix (e.g., `hr-docs-a7k2`)
- `drive_code` - Uses drive code (e.g., `hr-docs-usba1b2`)
- `sequential` - Sequential numbering
- `custom` - Custom suffix provided at creation

#### Bulk Update URL Configurations
```http
PUT /settings/url-configs/bulk

[
  {
    "id": "uuid",
    "enabled": true,
    "base_slug": "hr-docs",
    "suffix_mode": "random",
    "suffix_length": 4
  }
]
```

Response:
```json
{
  "updated": ["uuid1", "uuid2"],
  "count": 2
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid auth)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

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
