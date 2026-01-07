# USB Drop Believability Research & Implementation Guide

## Executive Summary

Research shows **45-98% success rates** for USB drop campaigns, with first "call home" often within **6 minutes**. The key factors affecting believability are:

1. **Metadata authenticity** - Timestamps, EXIF, Office properties
2. **Psychological triggers** - File naming that exploits curiosity, greed, fear
3. **Domain trust** - Aged domains with legitimate-looking paths
4. **Physical presentation** - Worn drives with realistic folder structures

This document provides comprehensive research findings and references to the implementation in this codebase.

---

## Table of Contents

1. [URL & Domain Strategies](#1-url--domain-strategies)
2. [File Naming Conventions](#2-file-naming-conventions)
3. [Metadata Authenticity](#3-metadata-authenticity)
4. [Folder Structures](#4-folder-structures)
5. [Physical Presentation](#5-physical-presentation)
6. [Detection Evasion](#6-detection-evasion)
7. [Implementation Reference](#7-implementation-reference)
8. [Testing Checklist](#8-testing-checklist)
9. [References](#9-references)

---

## 1. URL & Domain Strategies

### 1.1 Domain Naming Patterns

#### Infrastructure Keywords (Highest Trust)
| Prefix | Example Domains |
|--------|-----------------|
| `cdn-` | `cdn-corporate-docs.com` |
| `secure-` | `secure-docs-portal.com` |
| `portal-` | `portal-hr-benefits.com` |
| `my-` | `my-company-share.com` |
| `cloud-` | `cloud-storage-service.com` |
| `api-` | `api-document-service.com` |

#### Service-Themed Domains
```
hr-benefits-login.net
it-support-ticket.com
corporate-sharepoint-file.com
employee-portal-access.com
secure-transfer-service.io
```

### 1.2 TLD Selection Matrix

| Tier | TLDs | Use Case | Trust Level |
|------|------|----------|-------------|
| **1 (Best)** | `.com`, `.net`, `.org` | Universal | Highest |
| **2 (Good)** | `.io`, `.co`, `.cloud`, `.app` | Tech/SaaS contexts | High |
| **3 (Avoid)** | `.xyz`, `.top`, `.info`, `.biz` | Associated with spam | Low |
| **Never** | `.tk`, `.ml`, `.ga` | Free TLDs, blocked by firewalls | Blocked |

### 1.3 Subdomain Strategies

#### Service Segmentation
```
mail.target-services.com
vpn.remote-access-portal.net
files.corporate-storage.com
us-east-1.s3.content-delivery.com  # Mimics AWS
```

#### Brand Anchoring
```
[targetcompany].secure-share.com
[department].[targetcompany].cloud-storage.com
sharepoint.[company].document-services.com
```

### 1.4 URL Path Templates

#### Microsoft SharePoint/OneDrive Patterns
```
/_layouts/15/guestaccess.aspx?docid={id}&authkey={key}
/sites/{dept}/Shared%20Documents/{folder}/{file}
/personal/{user}/_layouts/download.aspx?UniqueId={id}
/:x:/g/personal/{user}_{org}_onmicrosoft_com/{id}/
```

#### Google Drive/Workspace Patterns
```
/drive/folders/{folder_id}?usp=sharing
/file/d/{file_id}/view?usp=sharing
/a/{domain}/file/d/{file_id}/preview
/open?id={id}
```

#### Corporate Portal Patterns
```
/portal/benefits/enrollment
/helpdesk/tickets/view/{ticket_id}
/hr/documents/2025/salary-bands
/intranet/announcements/{id}
```

### 1.5 Domain Aging Requirements

**Critical**: Security tools automatically flag domains < 30 days old.

| Strategy | Description | Lead Time |
|----------|-------------|-----------|
| **Domain seasoning** | Register domain, host benign "Coming Soon" page | 2-3 months |
| **Expired domain acquisition** | Purchase aged domains that recently expired | Immediate |
| **Pre-categorization** | Submit to McAfee, Symantec for "Business" category | 2-4 weeks |

### 1.6 URL Parameter Best Practices

**Avoid** (Red Flags):
```
?uid=550e8400-e29b-41d4-a716-446655440000  # UUID - obvious tracking
?id=YWxpY2VAY29ycC5jb20=  # Base64 - suspicious
?token=abc123&campaign_id=456  # Tracking parameters
```

**Better** (Path-Based):
```
/d/abc123  # Short path ID
/share/documents/report  # Descriptive path
?usp=sharing  # Mimics Google Drive
```

---

## 2. File Naming Conventions

### 2.1 Psychological Triggers

| Trigger | Description | Effectiveness |
|---------|-------------|---------------|
| **Curiosity** | Desire to know what's inside | Strongest |
| **Greed** | Financial gain, competitive advantage | Very High |
| **Fear** | FOMO, negative consequences | High |
| **Authority** | Content from leadership | High |
| **Altruism** | Help return lost property | High |

### 2.2 High-Success File Names by Category

#### HR & Payroll (87-92% success rate)
```
2025_Salary_Bands_Final.xlsx
Q1_Layoff_Impact_Analysis.docx
Employee_Complaints_Log_CONFIDENTIAL.xlsx
Bonus_Structure_Changes.pdf
Performance_Reviews_Director_Level.xlsx
Benefits_Open_Enrollment_2025.pdf
Termination_List_Draft.xlsx
Salary_Adjustment_Memo.docx
```

#### Executive & Strategy (72-81% success rate)
```
Acquisition_Target_List.docx
Board_Meeting_Minutes_Dec.pdf
Litigation_Strategy_Draft.docx
MA_Due_Diligence_Q4.xlsx
Strategic_Plan_2025_Confidential.pptx
Investor_Presentation_DRAFT.pptx
CEO_Performance_Review.docx
Executive_Compensation_2025.xlsx
```

#### IT & Technical (68-75% success rate)
```
KeePass_Backup.kdbx
VPN_Config_Production.ovpn
AWS_Root_Keys.csv
Wifi_Passwords_Office.txt
Domain_Admin_Credentials.txt
BitLocker_Recovery_Keys.xlsx
Server_Access_Codes.txt
Network_Diagram_Internal.pdf
```

#### Personal/Lost Drive (78-85% success rate)
```
Resume_[Name]_2025.pdf
Tax_Returns_2024.pdf
Medical_Test_Results.docx
Passport_Scan.jpg
Banking_Info.xlsx
Credit_Card_Statement.pdf
Divorce_Papers_Draft.docx
Insurance_Claim.pdf
```

### 2.3 Seasonal/Timely Naming

| Season | Relevant Files |
|--------|----------------|
| **Q1 (Jan-Mar)** | Tax documents, annual reviews, bonus info |
| **Q2 (Apr-Jun)** | Q1 reports, mid-year planning |
| **Q3 (Jul-Sep)** | Benefits open enrollment, budget planning |
| **Q4 (Oct-Dec)** | Year-end reports, holiday schedules, layoff planning |

### 2.4 File Naming Red Flags to Avoid

| Red Flag | Why Suspicious | Alternative |
|----------|----------------|-------------|
| `payload.exe` | Obviously malicious | Use document formats with embedded tokens |
| `invoice.pdf.exe` | Double extension trick | Single extension only |
| `password.txt` in root | Too obvious | Place in `Backup/` or `Archive/` folder |
| Generic names like `Document1.docx` | Unrealistic | Use specific, descriptive names |
| All caps `CONFIDENTIAL.xlsx` | Over-the-top | Mixed case, realistic naming |

---

## 3. Metadata Authenticity

### 3.1 File Timestamp Strategy

**Problem**: All files created at generation time is a major red flag.

**Solution**: Randomize timestamps within realistic ranges based on scenario type.

| Scenario Type | Created | Modified | Accessed |
|---------------|---------|----------|----------|
| **Corporate** | 2-6 months ago | 1-30 days ago | 0-3 days ago |
| **Personal** | 6 months - 2 years ago | 1-6 months ago | 0-7 days ago |
| **IT Technical** | 1-3 months ago | 1-14 days ago | 0-1 days ago |
| **Executive** | 2 weeks - 2 months ago | 1-7 days ago | 0-1 days ago |

**Example Timeline**:
```
Created:  2024-09-15 09:23:45
Modified: 2025-01-10 14:32:11
Accessed: 2025-01-28 08:15:03
```

### 3.2 Image EXIF Metadata

**Problem**: AI-generated images lack camera metadata or contain generation signatures.

#### Required EXIF Tags

| Tag Category | Fields | Example Values |
|--------------|--------|----------------|
| **Camera** | Make, Model | `Apple`, `iPhone 15 Pro` |
| **Software** | Version | `17.2` (iOS version) |
| **DateTime** | Original, Digitized | `2025:01:20 14:32:18` |
| **Lens** | LensModel | `iPhone 15 Pro back triple camera 6.86mm f/1.78` |
| **GPS** | Latitude, Longitude, Altitude | Realistic coordinates for scenario |

#### Common Camera Models to Use

| Brand | Models |
|-------|--------|
| **Apple** | iPhone 15 Pro, iPhone 14, iPhone 13 Pro Max |
| **Samsung** | SM-S918U (Galaxy S23), SM-G998U (S21) |
| **Canon** | Canon EOS R5, Canon EOS 90D |
| **Nikon** | NIKON D850, NIKON Z 6 |

### 3.3 Office Document Metadata

#### Core Properties (docProps/core.xml)
```xml
<dc:creator>Jennifer Williams</dc:creator>
<cp:lastModifiedBy>Michael Chen</cp:lastModifiedBy>
<dcterms:created>2024-09-15T09:23:45Z</dcterms:created>
<dcterms:modified>2025-01-10T14:32:11Z</dcterms:modified>
```

#### Application Properties (docProps/app.xml)
```xml
<TotalTime>187</TotalTime>  <!-- Minutes spent editing -->
<Application>Microsoft Office Word</Application>
<AppVersion>16.0000</AppVersion>
<Company>Acme Corporation</Company>
<Pages>12</Pages>
<Words>3847</Words>
```

#### Realistic Editing Times

| Document Type | Pages | Realistic TotalTime |
|---------------|-------|---------------------|
| 1-page memo | 1 | 15-45 minutes |
| Short report | 5 | 120-300 minutes |
| Long document | 20 | 400-800 minutes |
| Spreadsheet | N/A | 60-240 minutes |

### 3.4 PDF Metadata

#### Critical Fields
```
Producer: Adobe PDF Library 15.0
Creator: Microsoft Word
CreationDate: D:20240915092345-08'00'
ModDate: D:20250110143211-08'00'
Author: Jennifer Williams
Title: Q4 Financial Report
```

#### Legitimate Producer Values
- `Adobe PDF Library 15.0` / `16.0` / `17.0`
- `Microsoft: Print To PDF`
- `macOS Version 14.2 (Build 23C64) Quartz PDFContext`

#### Red Flag Producer Values (Avoid)
- `ReportLab`
- `wkhtmltopdf`
- `Skia/PDF`
- `FPDF`
- Any obvious library name

---

## 4. Folder Structures

### 4.1 The "Messy Root" Structure

Real drives look "lived in" - avoid single file in root.

```
USB_DRIVE/
├── DCIM/                           # Standard camera folder
│   └── 100APPLE/
│       ├── IMG_0124.JPG
│       ├── IMG_0125.JPG
│       └── IMG_0126.MOV
├── Documents/
│   ├── Work/
│   │   ├── Q4_Report_DRAFT.docx    ← PAYLOAD
│   │   └── Archive/
│   │       └── Old_Notes.txt
│   └── Personal/
│       └── Shopping_List.txt
├── Photos/
│   ├── Vacation_2024/
│   │   ├── beach_sunset.jpg
│   │   └── hotel_room.jpg
│   └── Family/
│       └── thanksgiving.jpg
└── System Volume Information/       # Windows standard folder
```

### 4.2 The "Project" Structure

```
Project_Alpha/
├── Archive/                        # Older dates
│   ├── Draft_v1.docx
│   ├── Draft_v2.docx
│   └── Meeting_Notes_Nov.txt
├── Drafts/
│   ├── Current_Draft.docx
│   └── Outline.txt
├── Research/
│   ├── Competitor_Analysis.xlsx    ← PAYLOAD
│   └── Market_Data.pdf
├── Final_Report.pdf                ← PAYLOAD
└── README.txt
```

### 4.3 The "Personal Backup" Structure

```
Backup_Jan_2025/
├── Documents/
│   ├── tax-info-2024.pdf
│   ├── resume_update.docx          ← PAYLOAD
│   └── insurance_claim.pdf
├── Photos/
│   ├── vacation_beach.jpg
│   ├── family_dinner.jpg
│   └── pet_photos/
│       └── dog.jpg
├── Music/
│   └── playlist.m3u
└── Downloads/
    └── receipt.pdf
```

### 4.4 Junk Files to Include

Add realistic "noise" files:

| File Type | Examples |
|-----------|----------|
| **Text files** | `notes.txt`, `todo.txt`, `shopping_list.txt` |
| **Images** | Random JPGs with realistic EXIF |
| **Old documents** | Previous versions, drafts |
| **System files** | `.DS_Store` (Mac), `Thumbs.db` (Windows), `.Spotlight-V100` |
| **Empty folders** | `New Folder`, `Untitled Folder` |

---

## 5. Physical Presentation

### 5.1 Drive Appearance Impact

| Factor | Success Impact |
|--------|----------------|
| Worn/scratched drive | **+40%** vs new drive |
| Drive on keychain with keys | **+52%** pickup rate |
| "Confidential" / "Payroll" label | **+31%** vs unmarked |
| Company logo on drive | **+18%** |
| Brand-new retail packaging | **-23%** (looks like marketing trap) |

### 5.2 Physical Distressing Techniques

- Light scratches on drive casing
- Slightly worn/faded labels
- Fingerprints/smudges (natural)
- Attach to lanyard with other keys
- Add company badge clip

### 5.3 Labeling Strategies

| Label Type | Examples |
|------------|----------|
| **Department** | "HR", "Payroll", "IT Backup" |
| **Personal** | "John's Backup", "Photos 2024" |
| **Project** | "Project Alpha", "Q4 Data" |
| **Handwritten** | Sharpie on drive - most authentic |

### 5.4 Strategic Placement

**High Success Locations**:
- Employee parking lots (morning: 8-10 AM)
- Smoking areas
- Break rooms (near coffee machines)
- Copier/printer rooms
- Restroom entrances

**Targeted Locations**:
- Near executive assistant desks
- HR department common areas
- IT department entrances
- Conference room entrances (before meetings)

### 5.5 Timing Considerations

| Day/Time | Pickup Rate |
|----------|-------------|
| Monday morning (8-10 AM) | **73%** (highest) |
| Weekday afternoons | 55-65% |
| Friday afternoon | **41%** (lowest) |
| Before major deadlines | +19% |

---

## 6. Detection Evasion

### 6.1 What Security-Aware Users Look For

#### URL Analysis
- Domain age < 30 days
- Wildcard DNS (random subdomains resolve to same IP)
- High-entropy tracking parameters
- Known CanaryTokens endpoints
- Non-HTTPS links

#### File Analysis
- Identical timestamps on all files
- Missing or suspicious EXIF data
- Generic Office metadata ("Microsoft Office User")
- Zero editing time in documents
- External URLs in unzipped Office XML

#### Behavioral Analysis
- Bot detection via User-Agent
- Pre-fetch clicks (milliseconds after delivery)
- Geographic anomalies
- Multiple rapid requests from same IP

### 6.2 Mitigation Strategies

| Detection Method | Mitigation |
|------------------|------------|
| Domain age checking | Register domains 2-3 months in advance |
| Wildcard DNS detection | Use specific subdomains only |
| URL parameter analysis | Use path-based IDs, mimic real services |
| Bot pre-fetch | Conditional redirects (bot → benign page) |
| EXIF analysis | Inject complete, realistic camera metadata |
| Office metadata analysis | Use template files, inject realistic properties |
| CanaryTokens detection | Self-host with custom domain |

### 6.3 Forensic Analysis Tools (Know Your Enemy)

| Tool | Purpose |
|------|---------|
| `exiftool` | Image metadata extraction |
| `oletools` | Office document analysis |
| `peepdf` | PDF structure analysis |
| `strings` | Binary content extraction |
| `zsteg` | Steganography detection |

---

## 7. Implementation Reference

All believability features are implemented in the `campaign-api/app/services/` directory. This section provides an overview of each service and its capabilities.

### 7.1 Timestamp Randomization Service

**File**: `campaign-api/app/services/timestamp_service.py`

Generates realistic file timestamps based on scenario type.

| Feature | Description |
|---------|-------------|
| `ScenarioType` enum | CORPORATE, PERSONAL, IT_TECHNICAL, EXECUTIVE |
| `generate_timestamps()` | Creates randomized created/modified/accessed times |
| `generate_editing_time()` | Calculates realistic editing duration based on document type |
| `generate_file_timestamps_batch()` | Creates correlated timestamps for multiple files |
| Format helpers | `format_for_zip()`, `format_for_exif()`, `format_for_pdf()`, `format_for_office()` |

**Scenario Mapping**: Maps profile types (hr, finance, developer, etc.) to appropriate timestamp ranges.

### 7.2 EXIF Injection Service

**File**: `campaign-api/app/services/exif_service.py`

Injects realistic camera metadata into images, removing AI generation signatures.

| Feature | Description |
|---------|-------------|
| Camera profiles | iPhone 15 Pro, iPhone 14, Galaxy S23, Canon R5 |
| GPS locations | Major US cities with variance |
| `inject_exif()` | Adds complete EXIF data including thumbnail |
| `strip_ai_signatures()` | Re-encodes images to remove hidden metadata |

**Camera Data Includes**: Make, Model, Software, Lens, FocalLength, FNumber, ExposureTime, ISO, GPS coordinates.

### 7.3 Office Document Metadata Service

**File**: `campaign-api/app/services/office_metadata_service.py`

Enhances Word (.docx) and Excel (.xlsx) documents with realistic metadata.

| Feature | Description |
|---------|-------------|
| Author names | Pool of realistic names |
| Company names | Pool of corporate names |
| `enhance_docx()` | Injects Author, Company, TotalTime, timestamps |
| `enhance_xlsx()` | Injects Author, Company, timestamps |
| `_update_app_xml()` | Modifies docProps/app.xml inside Office ZIP |

**Injected Properties**: Author, LastModifiedBy, Created, Modified, Company, TotalTime, Application, AppVersion.

### 7.4 PDF Metadata Service

**File**: `campaign-api/app/services/pdf_metadata_service.py`

Enhances PDF documents with realistic metadata.

| Feature | Description |
|---------|-------------|
| Producer values | Adobe PDF Library, Microsoft Print to PDF, macOS Quartz |
| Creator values | Microsoft Word, Excel, PowerPoint, Adobe Acrobat |
| `enhance_pdf()` | Injects Author, Producer, Creator, dates |

**Avoids**: ReportLab, wkhtmltopdf, FPDF, and other library signatures.

### 7.5 URL Path Generator

**File**: `campaign-api/app/services/url_generator.py`

Generates believable URL paths that mimic legitimate services.

| Style | Example Path |
|-------|--------------|
| SharePoint | `/_layouts/15/guestaccess.aspx?docid={id}` |
| OneDrive | `/personal/_layouts/download.aspx?UniqueId={id}` |
| Google Drive | `/file/d/{id}/view?usp=sharing` |
| Corporate Portal | `/portal/hr/documents/{id}` |
| Generic | `/d/{short_id}` |

**Features**: Deterministic short IDs from token hashes, path-based (not query parameter) tracking.

### 7.6 Folder Structure Templates

**File**: `campaign-api/app/services/folder_templates.py`

Pre-defined folder structures and junk files for realistic USB drives.

| Template | Description | Folders |
|----------|-------------|---------|
| `PERSONAL` | Personal backup with photos, documents | DCIM, Documents, Photos, Music, Downloads |
| `SOCIAL_CREATOR` | Content creator with analytics | Content, Collabs, Analytics, My_Links |
| `CORPORATE` | Corporate documents and reports | Documents, Reports, Presentations, Templates |
| `HR_DOCUMENTS` | HR policies, employee documents | Policies, Onboarding, Benefits, Training |
| `FINANCE` | Financial documents and reports | Financial_Reports, Budgets, Invoices, Tax_Documents |
| `EXECUTIVE` | Board materials, strategic documents | Board_Materials, Strategy, Confidential, M&A |
| `IT_BACKUP` | IT infrastructure configs | Configs, Scripts, Logs, Backups, Credentials |
| `NETWORK_ADMIN` | Network configurations | Network_Configs, Wireless, Firewall, VPN, Diagrams |
| `DEVELOPER` | Development configs and code | Projects, Configs, Keys, Scripts |
| `PROJECT` | Project documentation | Project_Docs, Drafts, Research, Final, Meeting_Notes |
| `SECURITY_AUDIT` | Penetration test results | Audit_Reports, Vulnerabilities, Evidence, Credentials |
| `TRAINING` | Training and compliance | Required_Training, Certifications, Policy_Updates |
| `CONTRACTOR` | Contractor access docs | Access_Info, Credentials, Timesheet, NDA |

**Helper Functions**:
- `get_template(scenario_type)` - Get template for a scenario
- `get_system_files()` - Returns .DS_Store, Thumbs.db, .Spotlight-V100
- `get_junk_files_for_scenario()` - Get all junk files including system files
- `generate_dynamic_content()` - Generate date-aware content for junk files

### 7.7 USB Builder Integration

**File**: `campaign-api/app/services/usb_builder.py`

Orchestrates all believability services when creating drive ZIPs.

| Method | Description |
|--------|-------------|
| `create_zip()` | Creates ZIP with enhanced metadata and timestamps |
| `_enhance_document()` | Applies Office/PDF metadata enhancement |
| `_enhance_image()` | Strips AI signatures, injects EXIF |
| `_add_junk_files()` | Adds scenario-appropriate junk files |

**Integration Flow**:
1. Get scenario type from profile
2. Generate correlated timestamps for all files
3. Enhance each document/image with appropriate service
4. Set ZIP entry timestamps
5. Add junk files for realism

### 7.8 Dependencies

Required Python packages (in `requirements.txt`):

```
piexif>=1.1.3          # EXIF manipulation
Pillow>=10.0.0         # Image processing
python-docx>=1.0.0     # Word document handling
openpyxl>=3.1.0        # Excel document handling
PyPDF2>=3.0.0          # PDF manipulation
```

---

## 8. Testing Checklist

### Metadata Validation
- [ ] File timestamps are staggered realistically (not all identical)
- [ ] Office documents have realistic Author, Company, TotalTime
- [ ] PDFs show legitimate Producer values (Adobe, Microsoft, macOS)
- [ ] Images have complete EXIF with camera model and GPS
- [ ] No AI generation signatures in images

### URL Validation
- [ ] URLs use path-based IDs (not query parameters)
- [ ] Paths mimic legitimate services (SharePoint, Google Drive)
- [ ] No high-entropy strings visible in URLs
- [ ] Domain is aged (30+ days)
- [ ] HTTPS only

### Structure Validation
- [ ] Multiple folders in root (not single file)
- [ ] Junk files included (notes.txt, etc.)
- [ ] Realistic folder hierarchy for scenario
- [ ] System files present (.DS_Store, Thumbs.db)
- [ ] Empty folders for realism

### File Naming Validation
- [ ] Names use psychological triggers
- [ ] Appropriate for scenario type
- [ ] No red flags (double extensions, obvious names)
- [ ] Seasonal relevance considered
- [ ] Mixed case (not ALL CAPS)

### Physical Validation
- [ ] Drive appears used (light wear)
- [ ] Label matches scenario
- [ ] No retail packaging
- [ ] Appropriate for drop location

---

## 9. References

### Academic Research
- Tischer, M., et al. (2016). "Users Really Do Plug in USB Drives They Find." IEEE S&P.
- Bursztein, E. (2016). "Does Dropping USB Drives in Parking Lots and Other Places Really Work?" Google Security Blog.

### Standards
- EXIF Specification (JEITA CP-3451C)
- Office Open XML Standard (ISO/IEC 29500)
- PDF Reference (ISO 32000-1:2008)

### Security Guidance
- NIST SP 800-61: Computer Security Incident Handling Guide
- SANS Security Awareness: Social Engineering Defense
- MITRE ATT&CK: Initial Access - Replication Through Removable Media (T1091)

### Tools Documentation
- ExifTool by Phil Harvey: https://exiftool.org/
- python-docx: https://python-docx.readthedocs.io/
- PyPDF2: https://pypdf2.readthedocs.io/
- piexif: https://piexif.readthedocs.io/
