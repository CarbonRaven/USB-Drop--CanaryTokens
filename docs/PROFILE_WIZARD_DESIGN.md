# Profile Wizard Design Document

## Overview

A multi-step wizard for creating, editing, and customizing USB drive profiles with integrated self-hosted URL shortening via Shlink.

**Status:** Implemented and operational.

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
│  │ /profiles/*  │  │ /shortener/* │  │ /drives/*    │          │
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

### Data Output
```javascript
{
  type: "hr",
  template_id: "hr_department",
  name: "HR Documents - Q4 Campaign",
  description: "Salary and benefits documents..."
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
│  │ └── 📁 Benefits             │  │ ☑ Make folder look enticing  ││
│  │                             │  │   (adds desktop.ini token)   ││
│  │ ─────────────────────────── │  │                              ││
│  │                             │  │ [Delete Folder]              ││
│  │ [+ Add Folder]              │  │                              ││
│  │                             │  │                              ││
│  └─────────────────────────────┘  └──────────────────────────────┘│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Component: VisualFileTree.vue

Displays an interactive file tree with:
- Folder hierarchy visualization
- Add/remove folder actions
- Folder token toggle

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
│  │ Token Types (TokenPalette)     Files in Profile             │  │
│  │                                                             │  │
│  │ ┌─────────────────────┐        ┌───────────────────┐       │  │
│  │ │ 📊 Excel Document   │        │ 📁 HR Documents   │       │  │
│  │ │ Triggers when opened│        │ ├ Salaries.xlsx ● │       │  │
│  │ └─────────────────────┘        │ ├ Benefits.docx ● │       │  │
│  │ ┌─────────────────────┐        │ └ desktop.ini  ●  │       │  │
│  │ │ 📝 Word Document    │        │ 📁 Payroll        │       │  │
│  │ │ Triggers when opened│        │ └ Paystubs.xlsx ● │       │  │
│  │ └─────────────────────┘        └───────────────────┘       │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 📕 PDF Document     │        ● = has token               │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐        [+ Add File]                │  │
│  │ │ 📁 Folder Token     │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 🔗 Web Link         │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  │ ┌─────────────────────┐                                    │  │
│  │ │ 📷 QR Code          │                                    │  │
│  │ └─────────────────────┘                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📤 File Upload                                               │  │
│  │ Upload custom documents, images, or other files             │  │
│  │ [Choose Files] or drag and drop                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Components

- **TokenPalette.vue** - Displays available token types
- **FileUploader.vue** - Handles file uploads to profile
- **TemplateEditor.vue** - Rich text editor for custom content with placeholder support

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
      name: "readme.txt",
      folder: "HR Documents",
      token_type: "url",
      custom_content: "Check salary info: {canary_token-URL}"
    }
  ]
}
```

---

## Step 4: Content & URL Shortening

### Purpose
Configure URL shortening settings, create shortcuts and templates, and set USB label suggestions.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 4: Content & Links                                            │
│ Customize content and configure short URLs                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 🔗 URL Shortener Configuration                               │  │
│  │                                                             │  │
│  │ ☑ Enable URL Shortening                                     │  │
│  │                                                             │  │
│  │ Base Slug: [hr-docs                    ]                    │  │
│  │                                                             │  │
│  │ Suffix Mode:                                                │  │
│  │   ● Random (e.g., hr-docs-x7k2)                            │  │
│  │   ○ Sequential (e.g., hr-docs-001)                         │  │
│  │   ○ Drive Code (e.g., hr-docs-usba1b2c3)                   │  │
│  │                                                             │  │
│  │ Suffix Length: [4] (for random mode)                        │  │
│  │                                                             │  │
│  │ Preview: https://links.yourdomain.com/hr-docs-x7k2          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 📝 Create Files                                              │  │
│  │                                                             │  │
│  │ [+ Create Shortcut]  [+ Create Template]                    │  │
│  │                                                             │  │
│  │ Note: Save profile first to enable file creation            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 🏷️ USB Drive Label Suggestions                               │  │
│  │                                                             │  │
│  │ [HR PAYROLL Q4    ] [CONFIDENTIAL] [+ Add]                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### URL Shortener Configuration

| Field | Description |
|-------|-------------|
| `enabled` | Toggle URL shortening on/off |
| `base_slug` | Base path for short URLs (e.g., "hr-docs") |
| `suffix_mode` | `random`, `sequential`, or `drive_code` |
| `suffix_length` | Length of random suffix (2-12 characters) |
| `domain` | Short URL domain (from Settings) |

### Shortcut Creation Modal

```
┌──────────────────────────────────────────────────────────────┐
│ Create URL Shortcut                                      [X] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Filename: [Company_Portal.url           ]                   │
│  Folder:   [HR Documents            ▼]                       │
│  Target URL: [https://example.com/login   ]                  │
│                                                              │
│  Shortcut Type:                                              │
│    ● Both (.url and .webloc)                                │
│    ○ Windows only (.url)                                    │
│    ○ macOS only (.webloc)                                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                              [Cancel]  [Create Shortcut]     │
└──────────────────────────────────────────────────────────────┘
```

### Template Creation Modal

```
┌──────────────────────────────────────────────────────────────┐
│ Create Text Template                                     [X] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Filename: [readme.txt                   ]                   │
│  Folder:   [HR Documents            ▼]                       │
│                                                              │
│  Content:                                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ IMPORTANT FILES                                        │  │
│  │ ==============                                         │  │
│  │                                                        │  │
│  │ Access salary data: {canary_token-URL}                 │  │
│  │ View benefits: {canary_token-URL}                      │  │
│  │                                                        │  │
│  │ Placeholders: {canary_token-URL}, {drive_code}         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                              [Cancel]  [Create Template]     │
└──────────────────────────────────────────────────────────────┘
```

### Data Output
```javascript
{
  url_shortener: {
    enabled: true,
    base_slug: "hr-docs",
    suffix_mode: "random",
    suffix_length: 4,
    domain: ""  // Uses default from Settings
  },
  label_suggestions: ["HR PAYROLL Q4", "CONFIDENTIAL"]
}
```

---

## Step 5: Review & Create

### Purpose
Review all configuration before creating/updating the profile.

### UI Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Step 5: Review & Create                                            │
│ Review your profile configuration before saving                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────┬───────────────────────┐ │
│  │ Profile Summary                      │ USB Preview           │ │
│  │                                      │                       │ │
│  │ Name: HR Documents - Q4 Campaign     │ 📁 USB Drive          │ │
│  │ Scenario: HR                         │ ├── 📁 HR Documents   │ │
│  │ Description: Salary and benefits...  │ │   ├── 📄 Salaries   │ │
│  │                                      │ │   ├── 📄 Benefits   │ │
│  │ ─────────────────────────────────    │ │   └── 📄 readme.txt │ │
│  │                                      │ ├── 📁 Payroll        │ │
│  │ 📁 Folders: 3                        │ │   └── 📄 Paystubs   │ │
│  │ 📄 Files: 5                          │ └── 📁 Benefits       │ │
│  │ 🎯 Tokens: 4                         │                       │ │
│  │ 📤 Uploaded: 2                       │ [Expand All]          │ │
│  │                                      │                       │ │
│  │ ─────────────────────────────────    │                       │ │
│  │                                      │                       │ │
│  │ URL Shortening: Enabled              │                       │ │
│  │ Base Slug: hr-docs                   │                       │ │
│  │ Suffix Mode: random                  │                       │ │
│  │                                      │                       │ │
│  └──────────────────────────────────────┴───────────────────────┘ │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Cancel]              [← Back]        [Save Profile]              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component Structure

```
src/
├── views/
│   └── Profiles.vue              # Contains wizard or links to it
│
├── components/
│   └── wizard/
│       ├── WizardProgress.vue    # Step indicator (1-5 dots)
│       ├── WizardNavigation.vue  # Back/Next/Cancel buttons
│       │
│       ├── ScenarioStep.vue      # Step 1 - Template selection
│       ├── FolderStep.vue        # Step 2 - Folder structure
│       ├── TokenStep.vue         # Step 3 - File/token config
│       ├── ContentStep.vue       # Step 4 - URLs & content
│       └── ReviewStep.vue        # Step 5 - Final review
│       │
│       ├── TokenPalette.vue      # Draggable token type cards
│       ├── VisualFileTree.vue    # Interactive file tree display
│       ├── FileUploader.vue      # File upload component
│       └── TemplateEditor.vue    # Rich text editor with placeholders
│
└── stores/
    └── profileWizard.js          # Pinia store (Composition API)
```

---

## State Management (Pinia)

**File**: `src/stores/profileWizard.js`

Uses Vue 3 Composition API style:

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProfileWizardStore = defineStore('profileWizard', () => {
  // Step management
  const currentStep = ref(1)
  const totalSteps = 5

  // Step 1: Scenario
  const scenario = ref({
    type: null,
    template_id: null,
    name: '',
    description: ''
  })

  // Step 2: Folders
  const folders = ref([])

  // Step 3: Files/Tokens
  const files = ref([])

  // Uploaded files (from API)
  const uploadedFiles = ref([])

  // Step 4: Content
  const content = ref({
    text_templates: {},
    url_shortener: {
      enabled: false,
      base_slug: '',
      suffix_mode: 'random',
      suffix_length: 4,
      domain: ''
    },
    images: {
      source: 'template',
      selected: []
    },
    label_suggestions: []
  })

  // Edit mode
  const isEditing = ref(false)
  const editingProfileId = ref(null)

  // Loading states
  const loading = ref(false)
  const saving = ref(false)

  // Computed
  const canProceed = computed(() => { /* validation logic */ })
  const tokenCount = computed(() => files.value.filter(f => f.token_type).length)
  const profileSummary = computed(() => ({ /* summary object */ }))

  // Actions
  function nextStep() { /* ... */ }
  function prevStep() { /* ... */ }
  async function loadTemplate(templateId) { /* ... */ }
  async function loadForEditing(profileId) { /* ... */ }
  async function saveProfile() { /* ... */ }

  // Folder management
  function addFolder(path) { /* ... */ }
  function removeFolder(path) { /* ... */ }
  function updateFolder(oldPath, newPath) { /* ... */ }

  // File management
  function addFile(file) { /* ... */ }
  function removeFile(index) { /* ... */ }
  function updateFile(index, updates) { /* ... */ }

  // Uploaded file management
  async function loadUploadedFiles(profileId) { /* ... */ }
  function addUploadedFile(file) { /* ... */ }
  async function removeUploadedFile(profileId, fileId) { /* ... */ }

  function reset() { /* ... */ }

  return {
    // State
    currentStep, totalSteps, scenario, folders, files,
    uploadedFiles, content, isEditing, editingProfileId,
    loading, saving,

    // Computed
    canProceed, tokenCount, profileSummary,

    // Actions
    nextStep, prevStep, loadTemplate, loadForEditing,
    saveProfile, addFolder, removeFolder, updateFolder,
    addFile, removeFile, updateFile, loadUploadedFiles,
    addUploadedFile, removeUploadedFile, reset
  }
})
```

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
│   │  Base Slug: hr-docs                                         │  │
│   │  Suffix Mode: random | sequential | drive_code              │  │
│   │  Suffix Length: 4                                           │  │
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
│   │  links.yourdomain.com/hr-docs-x7k2                          │  │
│   │  Unique CanaryToken → Unique Short URL                      │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   Drive USB-D4E5F6:                                                 │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  links.yourdomain.com/hr-docs-m9p4                          │  │
│   │  Unique CanaryToken → Unique Short URL                      │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### URL Suffix Modes

| Mode | Example | Use Case |
|------|---------|----------|
| **random** | `hr-docs-x7k9` | Default, hard to guess |
| **sequential** | `hr-docs-001` | Easy to track order |
| **drive_code** | `hr-docs-usba1b2c3` | Ties directly to drive ID |

### Generation Flow

```
Drive Creation Request
         │
         ▼
┌─────────────────────────┐
│ 1. Load Profile Config  │
│    - URL patterns       │
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
│     "hr-docs-x7k2"      │
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

---

## API Endpoints

### Profile Wizard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profiles/templates` | List available templates |
| GET | `/api/profiles/templates/{id}` | Get template details |
| POST | `/api/profiles` | Create profile |
| PUT | `/api/profiles/{id}` | Update profile |
| GET | `/api/profiles/{id}` | Get profile for editing |

### Profile Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profiles/{id}/files` | List uploaded files |
| POST | `/api/profiles/{id}/files` | Upload file |
| PUT | `/api/profiles/{id}/files/{fid}` | Update file metadata |
| DELETE | `/api/profiles/{id}/files/{fid}` | Delete file |
| POST | `/api/profiles/{id}/shortcuts` | Create URL shortcut |
| POST | `/api/profiles/{id}/templates` | Create text template |

### Shortener

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shortener/status` | Get Shlink status |
| GET | `/api/shortener/domains` | List available domains |
| POST | `/api/shortener/create` | Create short URL |
| DELETE | `/api/shortener/{code}` | Delete short URL |

---

## Database Schema

### Profile URL Configuration

```sql
-- Stored in profiles.url_config JSONB column
{
  "enabled": true,
  "base_slug": "hr-docs",
  "suffix_mode": "random",
  "suffix_length": 4,
  "domain": null  -- Uses default if null
}
```

### Short URLs Table

```sql
CREATE TABLE short_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drive_id UUID NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    token_id UUID REFERENCES tokens(id) ON DELETE CASCADE,

    -- Slug components
    base_slug VARCHAR(100) NOT NULL,
    suffix VARCHAR(50) NOT NULL,
    full_slug VARCHAR(150) NOT NULL,

    -- Shlink reference
    shlink_short_code VARCHAR(50) NOT NULL,
    shlink_domain VARCHAR(255) NOT NULL,

    -- URLs
    canary_url TEXT NOT NULL,
    short_url TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(shlink_domain, shlink_short_code)
);

CREATE INDEX idx_short_urls_drive ON short_urls(drive_id);
CREATE INDEX idx_short_urls_token ON short_urls(token_id);
```

---

## Implementation Status

### Phase 1: Core Wizard ✅
- [x] Wizard container and navigation
- [x] Step 1: Scenario selection with templates
- [x] Step 2: Folder management
- [x] Step 3: Token assignment
- [x] Step 5: Review and create
- [x] Integration with profile API
- [x] Edit existing profile flow

### Phase 2: Advanced Tokens ✅
- [x] TokenPalette component
- [x] File upload support (FileUploader)
- [x] Custom content with placeholders (TemplateEditor)
- [x] VisualFileTree component

### Phase 3: URL Shortener ✅
- [x] Shlink Docker integration
- [x] Shlink API client service
- [x] Step 4: URL shortener configuration
- [x] Short URL database model
- [x] URL generation on drive preparation
- [x] Settings page for Shlink configuration

### Phase 4: Content Features ✅
- [x] Shortcut creation (URL and webloc)
- [x] Template creation with placeholders
- [x] Label suggestions
- [x] Uploaded file management

### Future Enhancements
- [ ] Drag-and-drop folder reordering
- [ ] Drag-and-drop token assignment
- [ ] Clone profile functionality
- [ ] Keyboard shortcuts
- [ ] Bulk file operations

---

## Design Decisions

1. **Composition API**: Store uses Vue 3 Composition API for better TypeScript support and code organization.

2. **Flat Component Structure**: Components are in a single `wizard/` folder rather than nested by step, simplifying imports.

3. **Uploaded Files Separate**: Uploaded files are managed separately from template files, stored via API.

4. **URL Config on Profile**: URL shortening configuration is stored on the profile; actual short URLs are generated per-drive.

5. **Suffix Modes**: Three modes (random, sequential, drive_code) cover most use cases without complex per-token configuration.

6. **Edit Mode**: Same wizard handles both create and edit, with `isEditing` flag controlling behavior.

7. **Shortcut/Template Creation**: Requires saved profile (editingProfileId) since files are stored server-side.
