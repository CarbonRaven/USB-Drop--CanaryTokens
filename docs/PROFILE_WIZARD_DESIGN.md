# Profile Wizard Design Document

## Overview

A multi-step wizard for creating, editing, and customizing USB drive profiles with integrated self-hosted URL shortening via Shlink.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    ProfileWizard.vue                         ││
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐        ││
│  │  │ Step 1  │ Step 2  │ Step 3  │ Step 4  │ Step 5  │        ││
│  │  │Scenario │ Folder  │ Token   │ Content │ Review  │        ││
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Campaign API (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ /profiles/*  │  │ /shortener/* │  │ /tokens/*    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ PostgreSQL│   │  Shlink  │   │ CanaryTokens │
        │ Database │   │  (URLs)  │   │   (Tokens)   │
        └──────────┘   └──────────┘   └──────────────┘
```

---

## Wizard Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│   ○ ─────── ○ ─────── ○ ─────── ○ ─────── ●                       │
│   1         2         3         4         5                        │
│ Scenario  Folder   Tokens   Content   Review                       │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│                      [ Step Content Area ]                         │
│                                                                    │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Cancel]                              [← Back]  [Next →]          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Scenario Selection

### Purpose
Select a base template/scenario that pre-populates folders, files, and token recommendations.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 1: Choose a Scenario                                          │
│ Select a template that matches your target environment             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  🏢               │  │  💼               │  │  👔               │ │
│  │  HR Department    │  │  IT Department    │  │  Executive        │ │
│  │                   │  │                   │  │                   │ │
│  │  8 files          │  │  12 files         │  │  6 files          │ │
│  │  3 folders        │  │  4 folders        │  │  2 folders        │ │
│  │  4 tokens         │  │  6 tokens         │  │  3 tokens         │ │
│  │                   │  │                   │  │                   │ │
│  │  [Preview]        │  │  [Preview]        │  │  [Preview]        │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  💰               │  │  🎨               │  │  👩‍💻               │ │
│  │  Finance          │  │  Social Creator   │  │  Developer        │ │
│  │                   │  │                   │  │                   │ │
│  │  10 files         │  │  15 files         │  │  8 files          │ │
│  │  4 folders        │  │  5 folders        │  │  3 folders        │ │
│  │  5 tokens         │  │  7 tokens         │  │  4 tokens         │ │
│  │                   │  │                   │  │                   │ │
│  │  [Preview]        │  │  [Preview]        │  │  [Preview]        │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  ➕ Start from Scratch                                        │ │
│  │  Create a custom profile with no pre-populated content        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Profile Name: [HR Documents - Q4 Campaign          ]              │
│  Description:  [Salary and benefits documents for...  ]            │
└────────────────────────────────────────────────────────────────────┘
```

### Preview Modal

```
┌─────────────────────────────────────────────────────┐
│ HR Department Template                          [X] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📁 HR Documents                                    │
│  ├── 📄 Employee_Salaries_2024.xlsx    [Excel]     │
│  ├── 📄 Benefits_Overview.docx         [Word]      │
│  └── 📄 desktop.ini                    [Folder]    │
│  📁 Payroll                                         │
│  ├── 📄 Pay_Stubs_Template.xlsx        [Excel]     │
│  └── 📄 Tax_Forms_W2.pdf               [PDF]       │
│  📁 Onboarding                                      │
│  └── 📄 New_Hire_Checklist.docx        [Word]      │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  Tokens: 2 Excel, 2 Word, 1 PDF, 1 Folder          │
│  Recommended for: Corporate environments            │
│                                                     │
├─────────────────────────────────────────────────────┤
│                      [Use This Template]            │
└─────────────────────────────────────────────────────┘
```

### Data Output
```javascript
{
  scenario_type: "hr",
  name: "HR Documents - Q4 Campaign",
  description: "Salary and benefits documents...",
  template_id: "hr_department"
}
```

---

## Step 2: Folder Structure

### Purpose
Customize the folder hierarchy that will appear on the USB drive.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 2: Folder Structure                                           │
│ Organize folders as they will appear on the USB drive              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────┐  ┌──────────────────────────────┐│
│  │ Folder Tree                 │  │ Folder Properties            ││
│  │                             │  │                              ││
│  │ 📁 USB Drive (root)         │  │ Selected: HR Documents       ││
│  │ ├── 📁 HR Documents    ←    │  │                              ││
│  │ │   └── 📁 Confidential     │  │ Name: [HR Documents      ]   ││
│  │ ├── 📁 Payroll              │  │                              ││
│  │ └── 📁 Benefits             │  │ Icon: [📁 Default     ▼]     ││
│  │                             │  │                              ││
│  │ ─────────────────────────── │  │ ☑ Make folder look enticing  ││
│  │                             │  │   (adds desktop.ini token)   ││
│  │ [+ Add Folder]              │  │                              ││
│  │ [+ Add Subfolder]           │  │ [Delete Folder]              ││
│  │                             │  │                              ││
│  └─────────────────────────────┘  └──────────────────────────────┘│
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 💡 Tip: Drag folders to reorder. Right-click for more options│ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Interactions

- **Drag & Drop**: Reorder folders, move into subfolders
- **Right-click menu**: Rename, Delete, Add Subfolder, Duplicate
- **Double-click**: Rename inline
- **Checkbox**: Add folder token (desktop.ini) to specific folders

### Data Output
```javascript
{
  folders: [
    { path: "HR Documents", has_folder_token: true },
    { path: "HR Documents/Confidential", has_folder_token: false },
    { path: "Payroll", has_folder_token: true },
    { path: "Benefits", has_folder_token: false }
  ]
}
```

---

## Step 3: Token Configuration

### Purpose
Configure which files to create and what token types to embed in each.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 3: Token Configuration                                        │
│ Configure tracking tokens for each file                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Token Types                          Files in Profile       │  │
│  │                                                             │  │
│  │ ┌─────────────────────┐              ┌───────────────────┐ │  │
│  │ │ 📊 Excel Document   │              │ 📁 HR Documents   │ │  │
│  │ │ Triggers when opened│  ──drag──▶   │ ├ Salaries.xlsx ● │ │  │
│  │ │ in Microsoft Excel  │              │ ├ Benefits.docx ● │ │  │
│  │ └─────────────────────┘              │ └ desktop.ini  ●  │ │  │
│  │ ┌─────────────────────┐              │ 📁 Payroll        │ │  │
│  │ │ 📝 Word Document    │              │ └ Paystubs.xlsx ● │ │  │
│  │ │ Triggers when opened│              │ 📁 Benefits       │ │  │
│  │ │ in Microsoft Word   │              │ └ Guide.pdf    ●  │ │  │
│  │ └─────────────────────┘              └───────────────────┘ │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 📕 PDF Document     │              ● = has token         │  │
│  │ │ Triggers in Adobe   │                                    │  │
│  │ │ Acrobat Reader      │              [+ Add File]          │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 📁 Folder Token     │                                    │  │
│  │ │ Triggers when folder│                                    │  │
│  │ │ is browsed          │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 🔗 Web Link         │                                    │  │
│  │ │ URL shortcut file   │                                    │  │
│  │ │ with tracking       │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 📷 QR Code          │                                    │  │
│  │ │ Image with tracking │                                    │  │
│  │ │ QR code             │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### File Configuration Panel (appears when file selected)

```
┌──────────────────────────────────────────────────────────────┐
│ Configure: Employee_Salaries_2024.xlsx                   [X] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  File Name:   [Employee_Salaries_2024.xlsx    ]              │
│  Location:    [HR Documents              ▼]                  │
│  Token Type:  [📊 Excel Document         ▼]                  │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  Link Token Settings (for Web Link type)                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Token Behavior:                                        │  │
│  │   ○ Web Bug (silent tracking)                          │  │
│  │   ○ Fast Redirect (immediate redirect)                 │  │
│  │   ● Slow Redirect (fingerprint + redirect)             │  │
│  │                                                        │  │
│  │ Redirect URL:                                          │  │
│  │   ○ Google Drive    ○ SharePoint    ○ OneDrive         │  │
│  │   ○ Login Page      ○ Error Page    ● Custom           │  │
│  │   [https://drive.google.com/file/d/shared    ]         │  │
│  │                                                        │  │
│  │ ☑ Enable browser fingerprinting                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  [Delete File]                    [Cancel]  [Save Changes]   │
└──────────────────────────────────────────────────────────────┘
```

### Data Output
```javascript
{
  files: [
    {
      name: "Employee_Salaries_2024.xlsx",
      folder: "HR Documents",
      token_type: "ms_excel",
      token_config: {}
    },
    {
      name: "Exclusive_Content.url",
      folder: "My Links",
      token_type: "web_link",
      token_config: {
        behavior: "slow-redirect",
        redirect_url: "https://drive.google.com/...",
        browser_fingerprint: true
      }
    }
  ]
}
```

---

## Step 4: Content & URL Shortening

### Purpose
Configure content details, AI-generated images, and URL shortening for link tokens.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 4: Content & Links                                            │
│ Customize content and configure short URLs                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📝 Text File Templates                                       │  │
│  │                                                             │  │
│  │ my-links.txt uses template: [Social Links Template    ▼]   │  │
│  │                                                             │  │
│  │ ┌─────────────────────────────────────────────────────────┐ │  │
│  │ │ MY SOCIAL LINKS                                         │ │  │
│  │ │ ===============                                         │ │  │
│  │ │ Updated: December 31, 2025                              │ │  │
│  │ │                                                         │ │  │
│  │ │ Subscribe: {tracking_url}                               │ │  │
│  │ │ Exclusive: {tracking_url}                               │ │  │
│  │ │ ...                                                     │ │  │
│  │ └─────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 🔗 URL Shortener Configuration                               │  │
│  │                                                             │  │
│  │ Shortener:  ● Shlink (self-hosted)  ○ None  ○ Manual       │  │
│  │                                                             │  │
│  │ ┌─────────────────────────────────────────────────────────┐ │  │
│  │ │ Domain: [links.subproject55.com              ▼]         │ │  │
│  │ │                                                         │ │  │
│  │ │ URL Mappings:                                           │ │  │
│  │ │ ┌─────────────────────────────────────────────────────┐ │ │  │
│  │ │ │ Token              │ Short Path    │ Preview        │ │ │  │
│  │ │ ├────────────────────┼───────────────┼────────────────┤ │ │  │
│  │ │ │ Subscribe Link     │ [subscribe ]  │ links.../sub.. │ │ │  │
│  │ │ │ Exclusive Content  │ [exclusive ]  │ links.../exc.. │ │ │  │
│  │ │ │ Tip Me             │ [tip       ]  │ links.../tip   │ │ │  │
│  │ │ │ YouTube Channel    │ [youtube   ]  │ links.../you.. │ │ │  │
│  │ │ │ Merch Store        │ [merch     ]  │ links.../merch │ │ │  │
│  │ │ └─────────────────────────────────────────────────────┘ │ │  │
│  │ │                                                         │ │  │
│  │ │ [Auto-Generate Paths]  [Clear All]                      │ │  │
│  │ └─────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 🖼️ Images                                                    │  │
│  │                                                             │  │
│  │ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │  │
│  │ │ 📷        │ │ 📷        │ │ 📷        │ │ ➕         │    │  │
│  │ │ selfie1   │ │ selfie2   │ │ product   │ │ Add Image │    │  │
│  │ │ [Template]│ │ [Template]│ │ [AI Gen]  │ │           │    │  │
│  │ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │  │
│  │                                                             │  │
│  │ Source: ○ Template Images  ○ AI Generated  ○ Upload        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 🏷️ USB Drive Label Suggestions                               │  │
│  │                                                             │  │
│  │ [JESSICA'S STUFF    ] [BACKUP - DO NOT DELETE] [+ Add]     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### URL Shortener Domain Selector

```
┌────────────────────────────────────────────────┐
│ Select Domain                              [X] │
├────────────────────────────────────────────────┤
│                                                │
│  Available Domains:                            │
│                                                │
│  ● links.subproject55.com (default)           │
│  ○ files.subproject55.com                     │
│  ○ docs.subproject55.com                      │
│  ○ share.subproject55.com                     │
│                                                │
│  ─────────────────────────────────────────     │
│  [+ Add New Domain]                            │
│                                                │
├────────────────────────────────────────────────┤
│                              [Cancel] [Select] │
└────────────────────────────────────────────────┘
```

### Data Output
```javascript
{
  text_templates: {
    "my-links.txt": "social_links"
  },
  url_shortener: {
    enabled: true,
    provider: "shlink",
    domain: "links.subproject55.com",
    mappings: [
      { token_name: "Subscribe Link", path: "subscribe" },
      { token_name: "Exclusive Content", path: "exclusive" },
      { token_name: "Tip Me", path: "tip" }
    ]
  },
  images: {
    source: "template",
    selected: ["selfie1.jpg", "selfie2.jpg", "product.jpg"]
  },
  label_suggestions: ["JESSICA'S STUFF", "BACKUP - DO NOT DELETE"]
}
```

---

## Step 5: Review & Create

### Purpose
Review all configuration before creating the profile.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 5: Review & Create                                            │
│ Review your profile configuration before creating                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────┬───────────────────────┐ │
│  │ Profile Summary                      │ USB Preview           │ │
│  │                                      │                       │ │
│  │ Name: Social Creator - Jessica       │ 📁 USB Drive          │ │
│  │ Scenario: Social/Creator             │ ├── 📁 My_Links       │ │
│  │ Description: Influencer content...   │ │   └── 📄 my-links   │ │
│  │                                      │ ├── 📁 Photos         │ │
│  │ ─────────────────────────────────    │ │   ├── 🖼️ selfie1    │ │
│  │                                      │ │   ├── 🖼️ selfie2    │ │
│  │ 📁 Folders: 3                        │ │   └── 🖼️ product    │ │
│  │ 📄 Files: 8                          │ ├── 📁 Collabs        │ │
│  │ 🎯 Tokens: 6                         │ │   └── 📄 rates.pdf  │ │
│  │ 🔗 Short URLs: 5                     │ └── 📁 Exclusive      │ │
│  │                                      │     └── 📄 content    │ │
│  │ ─────────────────────────────────    │                       │ │
│  │                                      │ [Expand All]          │ │
│  │ Token Breakdown:                     │                       │ │
│  │ • 2x Word Documents                  │                       │ │
│  │ • 1x Excel Spreadsheet               │                       │ │
│  │ • 1x PDF Document                    │                       │ │
│  │ • 2x Web Links (slow redirect)       │                       │ │
│  │                                      │                       │ │
│  └──────────────────────────────────────┴───────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 🔗 Short URL Preview                                          │ │
│  │                                                              │ │
│  │  Token                  Short URL                            │ │
│  │  ───────────────────────────────────────────────────────────  │ │
│  │  Subscribe Link         https://links.subproject55.com/sub.. │ │
│  │  Exclusive Content      https://links.subproject55.com/exc.. │ │
│  │  Tip Me                 https://links.subproject55.com/tip   │ │
│  │  YouTube Channel        https://links.subproject55.com/you.. │ │
│  │  Merch Store            https://links.subproject55.com/merch │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ ⚠️  This will create 6 CanaryTokens and 5 short URLs          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Cancel]              [← Back]        [Create Profile]            │
│                                                                    │
│                        ☐ Create as draft (don't generate tokens)   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Shlink Integration

### Infrastructure Addition

```yaml
# docker-compose.yml addition
services:
  shlink:
    image: shlinkio/shlink:stable
    container_name: shlink
    restart: unless-stopped
    environment:
      DEFAULT_DOMAIN: links.subproject55.com
      IS_HTTPS_ENABLED: "true"
      GEOLITE_LICENSE_KEY: ${GEOLITE_LICENSE_KEY:-}
      DB_DRIVER: postgres
      DB_HOST: postgres
      DB_NAME: shlink
      DB_USER: shlink
      DB_PASSWORD: ${SHLINK_DB_PASSWORD}
      INITIAL_API_KEY: ${SHLINK_API_KEY}
    ports:
      - "8090:8080"
    depends_on:
      - postgres
    networks:
      - internal

  shlink-web:
    image: shlinkio/shlink-web-client:stable
    container_name: shlink-web
    restart: unless-stopped
    environment:
      SHLINK_SERVER_URL: https://links.subproject55.com
      SHLINK_SERVER_API_KEY: ${SHLINK_API_KEY}
    ports:
      - "8091:8080"
    networks:
      - internal
```

### Database Schema Addition

```sql
-- Add to existing schema
CREATE TABLE short_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    token_id UUID REFERENCES tokens(id) ON DELETE CASCADE,

    -- Shlink reference
    shlink_short_code VARCHAR(50) NOT NULL,
    shlink_domain VARCHAR(255) NOT NULL,

    -- URL details
    original_url TEXT NOT NULL,
    short_url TEXT NOT NULL,
    custom_slug VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    click_count INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMP,

    UNIQUE(shlink_domain, shlink_short_code)
);

CREATE INDEX idx_short_urls_profile ON short_urls(profile_id);
CREATE INDEX idx_short_urls_token ON short_urls(token_id);
```

### API Endpoints

```
POST   /api/shortener/domains          - List available domains
POST   /api/shortener/create           - Create short URL
GET    /api/shortener/profile/{id}     - Get short URLs for profile
DELETE /api/shortener/{short_code}     - Delete short URL
POST   /api/shortener/bulk-create      - Create multiple short URLs

GET    /api/profiles/{id}/with-urls    - Get profile with short URLs
POST   /api/profiles/{id}/regenerate-urls - Regenerate all short URLs
```

### Shlink Client Service

```python
# app/services/shlink_client.py

class ShlinkClient:
    """Client for self-hosted Shlink URL shortener."""

    def __init__(self):
        self.base_url = settings.shlink_url
        self.api_key = settings.shlink_api_key

    async def create_short_url(
        self,
        long_url: str,
        custom_slug: str = None,
        domain: str = None,
        tags: list = None
    ) -> dict:
        """Create a shortened URL."""
        pass

    async def delete_short_url(self, short_code: str, domain: str = None) -> bool:
        """Delete a short URL."""
        pass

    async def get_short_url_stats(self, short_code: str, domain: str = None) -> dict:
        """Get click statistics for a short URL."""
        pass

    async def list_domains(self) -> list:
        """List available domains."""
        pass
```

---

## Frontend State Management

### Pinia Store

```javascript
// stores/profileWizard.js

export const useProfileWizardStore = defineStore('profileWizard', {
  state: () => ({
    currentStep: 1,
    totalSteps: 5,

    // Step 1: Scenario
    scenario: {
      type: null,
      template_id: null,
      name: '',
      description: ''
    },

    // Step 2: Folders
    folders: [],

    // Step 3: Tokens
    files: [],

    // Step 4: Content
    content: {
      text_templates: {},
      url_shortener: {
        enabled: true,
        provider: 'shlink',
        domain: 'links.subproject55.com',
        mappings: []
      },
      images: {
        source: 'template',
        selected: []
      },
      label_suggestions: []
    },

    // Validation
    errors: {},

    // Edit mode
    isEditing: false,
    editingProfileId: null
  }),

  actions: {
    nextStep() { ... },
    prevStep() { ... },
    goToStep(step) { ... },
    validateCurrentStep() { ... },
    loadFromTemplate(templateId) { ... },
    loadForEditing(profileId) { ... },
    saveProfile() { ... },
    reset() { ... }
  },

  getters: {
    canProceed: (state) => { ... },
    profileSummary: (state) => { ... },
    tokenCount: (state) => { ... },
    shortUrlCount: (state) => { ... }
  }
})
```

---

## Component Structure

```
src/
├── views/
│   └── ProfileWizard.vue              # Main wizard container
│
├── components/
│   └── wizard/
│       ├── WizardProgress.vue         # Step indicator
│       ├── WizardNavigation.vue       # Back/Next/Cancel buttons
│       │
│       ├── steps/
│       │   ├── ScenarioStep.vue       # Step 1
│       │   ├── FolderStep.vue         # Step 2
│       │   ├── TokenStep.vue          # Step 3
│       │   ├── ContentStep.vue        # Step 4
│       │   └── ReviewStep.vue         # Step 5
│       │
│       ├── scenario/
│       │   ├── ScenarioCard.vue       # Scenario selection card
│       │   └── ScenarioPreview.vue    # Template preview modal
│       │
│       ├── folder/
│       │   ├── FolderTree.vue         # Drag-drop folder tree
│       │   ├── FolderNode.vue         # Individual folder node
│       │   └── FolderProperties.vue   # Folder settings panel
│       │
│       ├── token/
│       │   ├── TokenPalette.vue       # Draggable token types
│       │   ├── FileList.vue           # Files with tokens
│       │   ├── FileConfig.vue         # File configuration modal
│       │   └── LinkTokenConfig.vue    # Link-specific options
│       │
│       ├── content/
│       │   ├── TextTemplates.vue      # Text file templates
│       │   ├── UrlShortener.vue       # URL shortener config
│       │   ├── UrlMappingTable.vue    # Short URL mappings
│       │   ├── ImageSelector.vue      # Image selection
│       │   └── LabelSuggestions.vue   # USB label suggestions
│       │
│       └── review/
│           ├── ProfileSummary.vue     # Summary stats
│           ├── UsbPreview.vue         # File tree preview
│           └── ShortUrlPreview.vue    # Short URL list
│
└── stores/
    └── profileWizard.js               # Wizard state management
```

---

## API Service

```javascript
// services/api.js additions

export const profileWizardApi = {
  // Templates
  getTemplates: () => api.get('/profiles/templates/list'),
  getTemplate: (id) => api.get(`/profiles/templates/${id}`),

  // Shortener
  getShortenerDomains: () => api.get('/shortener/domains'),
  createShortUrl: (data) => api.post('/shortener/create', data),
  bulkCreateShortUrls: (data) => api.post('/shortener/bulk-create', data),
  deleteShortUrl: (code) => api.delete(`/shortener/${code}`),

  // Profile with URLs
  getProfileWithUrls: (id) => api.get(`/profiles/${id}/with-urls`),
  regenerateUrls: (id) => api.post(`/profiles/${id}/regenerate-urls`),

  // Wizard actions
  validateStep: (step, data) => api.post('/profiles/wizard/validate', { step, data }),
  createFromWizard: (data) => api.post('/profiles/wizard/create', data),
  updateFromWizard: (id, data) => api.put(`/profiles/wizard/${id}`, data)
}
```

---

## Environment Variables

```bash
# .env additions for Shlink

# Shlink URL Shortener
SHLINK_URL=http://shlink:8080
SHLINK_API_KEY=your-shlink-api-key
SHLINK_DEFAULT_DOMAIN=links.subproject55.com
SHLINK_DB_PASSWORD=your-shlink-db-password

# Optional: GeoLite2 for geographic stats
GEOLITE_LICENSE_KEY=your-maxmind-key
```

---

## Caddy Configuration

```caddyfile
# Add to Caddyfile for Shlink

links.subproject55.com {
    reverse_proxy shlink:8080
}

# Optional: Shlink admin UI
shlink-admin.subproject55.com {
    reverse_proxy shlink-web:8080

    # Restrict to admin IPs
    @blocked not remote_ip 10.0.0.0/8 192.168.0.0/16
    respond @blocked 403
}
```

---

## Implementation Phases

### Phase 1: Core Wizard (MVP)
- [ ] Wizard container and navigation
- [ ] Step 1: Scenario selection with templates
- [ ] Step 2: Basic folder management
- [ ] Step 3: Token assignment (no link config)
- [ ] Step 5: Review and create
- [ ] Integration with existing profile API

### Phase 2: Advanced Tokens
- [ ] Step 3: Link token configuration (redirect, fingerprint)
- [ ] Step 4: Text templates
- [ ] Step 4: Image selection
- [ ] Enhanced review with token breakdown

### Phase 3: URL Shortener
- [ ] Shlink Docker integration
- [ ] Shlink API client service
- [ ] Step 4: URL shortener configuration
- [ ] Short URL database model
- [ ] Bulk short URL creation on profile save

### Phase 4: Polish
- [ ] Drag-and-drop folder tree
- [ ] Drag-and-drop token assignment
- [ ] Real-time validation
- [ ] Edit existing profile flow
- [ ] Clone profile functionality
- [ ] Keyboard shortcuts

---

## Design Decisions

1. **Domain Management**: Admin-only. Regular users select from pre-configured domains in a dropdown. Admins manage domains via Shlink admin UI or dedicated admin settings page.

2. **Short URL Lifecycle**: Delete short URLs when drive is deleted. Cascade delete via foreign key relationship. Short URLs belong to drives, not profiles.

3. **Click Analytics**: No. Click stats are not displayed in the campaign dashboard. Use Shlink admin UI for URL analytics if needed.

4. **Bulk Operations**: Yes. Provide ability to apply the same short URL domain/pattern across multiple profiles (e.g., "Apply `hr.company.link` domain to all HR profiles").

5. **Slug Validation**: Yes. Real-time validation of short URL slugs for conflicts before the final step. Show inline error if slug already exists on selected domain.

6. **Unique URLs Per Drive**: Yes. Each drive created from a profile generates unique short URLs. Profile defines the pattern/template; drive creation generates unique instances.

---

## URL Generation Model

### Profile vs Drive URL Relationship

```
┌─────────────────────────────────────────────────────────────────────┐
│                           PROFILE                                   │
│                    (Template / Blueprint)                           │
│                                                                     │
│   Defines URL Pattern:                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  Domain: links.company.com                                   │  │
│   │  Base Slug: salary-info                                      │  │
│   │  Suffix Mode: [random | sequential | drive-code]             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Creates
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DRIVES                                    │
│                    (Unique Instances)                               │
│                                                                     │
│   Drive USB-A1B2C3:                                                 │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  links.company.com/salary-info-a1b2c3                        │  │
│   │  Unique CanaryToken → Unique Short URL                       │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   Drive USB-D4E5F6:                                                 │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  links.company.com/salary-info-d4e5f6                        │  │
│   │  Unique CanaryToken → Unique Short URL                       │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   Drive USB-G7H8I9:                                                 │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  links.company.com/salary-info-g7h8i9                        │  │
│   │  Unique CanaryToken → Unique Short URL                       │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### URL Suffix Modes

| Mode | Example | Use Case |
|------|---------|----------|
| **Random** | `salary-info-x7k9m2` | Default, hard to guess |
| **Sequential** | `salary-info-001`, `salary-info-002` | Easy to track order |
| **Drive Code** | `salary-info-USB-A1B2C3` | Ties directly to drive ID |
| **Custom** | User-defined per drive | Special cases |

### Generation Flow

```
Drive Creation Request
         │
         ▼
┌─────────────────────────┐
│ 1. Load Profile Config  │
│    - URL patterns       │
│    - Domain             │
│    - Suffix mode        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Generate Drive Code  │
│    USB-A1B2C3           │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. For Each Link Token: │
│                         │
│  a. Create CanaryToken  │
│     → Get unique URL    │
│                         │
│  b. Generate Short Slug │
│     base + suffix       │
│     "salary-info-a1b2c3"│
│                         │
│  c. Create Shlink URL   │
│     Short → Canary URL  │
│                         │
│  d. Store mapping       │
│     in short_urls table │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Build USB Content    │
│    - Replace {url}      │
│      placeholders with  │
│      unique short URLs  │
└─────────────────────────┘
```

### Updated Database Schema

```sql
-- Profile stores URL templates/patterns
ALTER TABLE profiles ADD COLUMN url_config JSONB DEFAULT '{}';

-- Example url_config:
-- {
--   "domain": "links.company.com",
--   "suffix_mode": "drive-code",  -- random | sequential | drive-code | custom
--   "patterns": [
--     { "token_name": "Subscribe Link", "base_slug": "subscribe" },
--     { "token_name": "Exclusive Content", "base_slug": "exclusive" }
--   ]
-- }

-- Short URLs belong to DRIVES, not profiles
CREATE TABLE short_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drive_id UUID NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    token_id UUID NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,

    -- Pattern source (from profile)
    base_slug VARCHAR(100) NOT NULL,
    suffix_mode VARCHAR(20) NOT NULL,

    -- Generated values
    generated_suffix VARCHAR(50) NOT NULL,
    full_slug VARCHAR(150) NOT NULL,  -- base_slug + generated_suffix

    -- Shlink reference
    shlink_short_code VARCHAR(50) NOT NULL,
    shlink_domain VARCHAR(255) NOT NULL,

    -- URLs
    canary_url TEXT NOT NULL,         -- Original CanaryToken URL
    short_url TEXT NOT NULL,          -- Final short URL

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(shlink_domain, shlink_short_code)
);

CREATE INDEX idx_short_urls_drive ON short_urls(drive_id);
CREATE INDEX idx_short_urls_token ON short_urls(token_id);
```

### Wizard Step 4 Update

```
┌────────────────────────────────────────────────────────────────────┐
│ 🔗 URL Shortener Configuration                                     │
│                                                                    │
│ These settings define URL PATTERNS. Unique URLs are generated     │
│ for each drive created from this profile.                         │
│                                                                    │
│ Domain: [links.company.com                    ▼]                   │
│                                                                    │
│ Suffix Mode:                                                       │
│   ● Random (e.g., salary-info-x7k9m2)                             │
│   ○ Sequential (e.g., salary-info-001)                            │
│   ○ Drive Code (e.g., salary-info-USB-A1B2)                       │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐│
│ │ Token              │ Base Slug      │ Example Output           ││
│ ├────────────────────┼────────────────┼──────────────────────────┤│
│ │ Subscribe Link     │ [subscribe  ]  │ .../subscribe-{suffix}   ││
│ │ Exclusive Content  │ [exclusive  ]  │ .../exclusive-{suffix}   ││
│ │ Tip Me             │ [tip        ]  │ .../tip-{suffix}         ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                    │
│ Preview (example drive USB-A1B2C3):                               │
│   • links.company.com/subscribe-a1b2c3                            │
│   • links.company.com/exclusive-a1b2c3                            │
│   • links.company.com/tip-a1b2c3                                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### DriveDetail View - Short URLs Section

```
┌────────────────────────────────────────────────────────────────────┐
│ Drive: USB-A1B2C3                                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 🔗 Short URLs (unique to this drive)                               │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐│
│ │ Token              │ Short URL                        │ Copy  ││
│ ├────────────────────┼──────────────────────────────────┼───────┤│
│ │ Subscribe Link     │ links.company.com/subscribe-a1b2 │ [📋]  ││
│ │ Exclusive Content  │ links.company.com/exclusive-a1b2 │ [📋]  ││
│ │ Tip Me             │ links.company.com/tip-a1b2       │ [📋]  ││
│ │ YouTube            │ links.company.com/youtube-a1b2   │ [📋]  ││
│ │ Merch Store        │ links.company.com/merch-a1b2     │ [📋]  ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                    │
│ [Copy All URLs]  [Regenerate URLs]                                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```
