# Profile Creation Wizard Research

## Implementation Status

> **Note:** This document contains research conducted during the design phase of the Profile Wizard. The wizard has been implemented based on these findings. See [PROFILE_WIZARD_DESIGN.md](PROFILE_WIZARD_DESIGN.md) for the actual implementation details.

**Decisions Made:**
- ✅ **5-step wizard** implemented (Scenario → Folders → Files/Tokens → Content → Review)
- ✅ **Shlink selected** for URL shortening (self-hosted, full control)
- ✅ **Slow redirect tokens** used as default for maximum intelligence gathering
- ✅ **Visual file tree** implemented for folder structure preview
- ✅ **URL path customization** available via profile file configuration
- ⏸️ **Power user mode** deferred (single-page with shortcuts)
- ⏸️ **WYSIWYG visual builder** deferred (drag-drop file explorer interface)

---

## Current State Analysis

The existing profile creation has:
- Template gallery with 12 pre-built scenarios
- "Quick Create" for instant profile creation from template
- Single-page modal for customization (name, folders, files, tokens)
- File-by-file token type selection

**Pain Points:**
- Dense single-page interface with many options
- No visual preview of USB structure
- No guidance on optimal token combinations
- Limited drag-and-drop functionality

---

## Recommended Wizard Approach

Based on [UX best practices](https://www.eleken.co/blog-posts/wizard-ui-pattern-explained), a **4-5 step wizard** is optimal:

### Step 1: Scenario Selection (Visual Cards)
- Large visual cards for each scenario type
- Show icon, name, description, file/folder count
- Preview thumbnail of typical USB structure
- "Recommended for: [target audience]" hints

### Step 2: Folder Structure (Tree Builder)
- Interactive [drag-and-drop tree view](https://next.jqueryscript.net/shadcn-ui/tree-view-drag/)
- Pre-populated from template, fully editable
- Add/rename/delete/reorder folders
- Visual folder icons with expand/collapse
- Components like [Shadcn Tree View](https://next.jqueryscript.net/shadcn-ui/hierarchical-data-tree-view/) or [Magic UI File Tree](https://magicui.design/docs/components/file-tree)

### Step 3: Token Configuration (Smart Defaults)
- Token type selection with visual icons
- Grouped by category: Documents, Images, Text, System
- Show effectiveness rating per scenario
- Auto-suggest token placement based on scenario
- Drag tokens onto folders in tree preview

### Step 4: Content Customization
- Text template selection for text files
- Image selection (template images or AI-generated)
- URL style configuration (SharePoint, OneDrive, etc.)
- Label suggestions for USB drive

### Step 5: Review & Create
- Full file tree preview (like current Preview modal)
- Token summary with counts
- Estimated "believability" score
- Create button with loading state

---

## UI Component Recommendations

| Feature | Component Options |
|---------|------------------|
| Step Progress | Horizontal stepper with icons, clickable for navigation |
| Folder Tree | [Reka UI Tree](https://reka-ui.com/docs/components/tree) or [Shadcn Tree View](https://next.jqueryscript.net/shadcn-ui/tree-view-drag/) |
| Token Cards | Draggable cards with icons, grouped by type |
| Preview | Split-pane with tree on left, details on right |
| Navigation | Sticky bottom bar: Back / Next / Cancel |

---

## Alternative Approaches

### Option A: Guided Wizard (Recommended for new users)
- Sequential steps as described above
- Conditional logic shows relevant options based on scenario
- Progress saved between steps
- Estimated completion: 2-3 minutes

### Option B: Power User Mode
- Single-page with collapsible sections
- Keyboard shortcuts for common actions
- Bulk file operations
- Template cloning with diff view
- For users who create profiles frequently

### Option C: Visual Builder (Most Engaging)
- WYSIWYG USB drive preview
- Drag files directly onto visual folder structure
- Right-click context menus
- Real-time preview updates
- Similar to file explorer interface

---

## Key Design Principles

Per [wizard design best practices](https://uxplanet.org/wizard-design-pattern-8c86e14f2a38):

1. **3-5 steps maximum** - Avoid overwhelming users
2. **Clear progress indicator** - Show where they are
3. **Back/Cancel always available** - Let users escape or revise
4. **Single-column layout** - Reduce cognitive load
5. **Validation per step** - Catch errors early
6. **Responsive design** - Support tablet/mobile use

---

## Implementation Priority

| Priority | Feature | Effort |
|----------|---------|--------|
| High | Step wizard framework | Medium |
| High | Visual folder tree | Medium |
| Medium | Drag-drop tokens | Medium |
| Medium | Live preview pane | Low |
| Low | Power user mode | High |
| Low | WYSIWYG builder | High |

---

## Existing Libraries to Consider

- [Vuestic Admin](https://admin.vuestic.dev/) - Vue 3 + Tailwind with wizard components
- [TailAdmin Vue](https://tailadmin.com/vue) - Free Vue 3 + Tailwind template
- [vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) - Production-ready admin patterns

---

## CanaryTokens Link Token Customization Options

This section documents the various ways link/URL tokens can be customized in CanaryTokens for integration into the profile wizard.

### Link Token Types

CanaryTokens offers three primary URL-based token types with different capabilities:

| Token Type | API Kind | Browser Fingerprint | Redirect Support | Use Case |
|------------|----------|---------------------|------------------|----------|
| **Web Bug (HTTP)** | `http` | Optional (JS scanner) | No | Silent tracking, embedded images |
| **Fast Redirect** | `fast-redirect` | No | Yes (immediate) | Quick redirect, less detection risk |
| **Slow Redirect** | `slow-redirect` | Yes (full scan) | Yes (after scan) | Maximum intelligence gathering |

### URL Path Customization

A key feature of CanaryTokens is **flexible URL path customization**. The token URL can be modified to appear as any file type or path:

**Base URL Example:**
```
http://45e51129ec7e.o3n.io/images/o63277vnjf6nfobn3cbey69fh/spacer.gif
```

**Can be changed to:**
```
http://45e51129ec7e.o3n.io/images/o63277vnjf6nfobn3cbey69fh/admin.asp
http://45e51129ec7e.o3n.io/images/o63277vnjf6nfobn3cbey69fh/secrets.docx
http://45e51129ec7e.o3n.io/images/o63277vnjf6nfobn3cbey69fh/passwords.zip
http://45e51129ec7e.o3n.io/images/o63277vnjf6nfobn3cbey69fh/backup.sql
```

All variations trigger the same token alert. This allows URLs to be disguised as:
- Document downloads (`.docx`, `.xlsx`, `.pdf`)
- Backup files (`.zip`, `.sql`, `.bak`)
- Admin pages (`.asp`, `.php`, `.aspx`)
- API endpoints (`/api/v1/users`, `/admin/config`)
- Resource files (`/images/logo.png`, `/assets/styles.css`)

### API Parameters for Link Tokens

When creating link tokens via the [Factory API](https://docs.canary.tools/canarytokens/factory.html):

#### Core Parameters (All Token Types)
| Parameter | Type | Description |
|-----------|------|-------------|
| `factory_auth` | string | Authentication token (required) |
| `kind` | string | Token type: `http`, `fast-redirect`, `slow-redirect` |
| `memo` | string | Alert description/identifier |
| `email` | string | Email for alerts (optional if webhook configured) |
| `webhook_url` | string | Webhook endpoint for alerts |

#### Redirect Parameters (Fast/Slow Redirect Only)
| Parameter | Type | Description |
|-----------|------|-------------|
| `browser_redirect_url` | string | **Required.** URL to redirect after trigger |

#### Browser Scanning (HTTP Token)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `browser_scanner_enabled` | boolean | `true` | Enable JavaScript scanner for browser/plugin info |

#### Advanced Options (Commercial/Enterprise)
| Parameter | Type | Description |
|-----------|------|-------------|
| `custom_domain` | string | Use pre-linked custom domain instead of default |
| `expected_referrer` | string | Validate request origin (for cloned-web tokens) |

### Redirect URL Strategies

For redirect tokens, the destination URL can serve different purposes:

#### 1. Legitimate-Looking Destinations
```
https://drive.google.com/file/d/shared-doc
https://sharepoint.com/sites/hr/documents
https://onedrive.live.com/download?id=file
https://dropbox.com/s/abc123/document.pdf
```

#### 2. Error/Login Pages (Increases Believability)
```
https://login.microsoftonline.com/
https://accounts.google.com/signin
https://auth.company.com/session-expired
```

#### 3. Rickroll / Obvious Detection
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://company.com/you-got-caught
```

#### 4. Custom Landing Pages
```
https://app.yourdomain.com/landing/session-expired
https://app.yourdomain.com/landing/file-not-found
https://app.yourdomain.com/landing/access-denied
```

### Browser Fingerprint Data (Slow Redirect)

The slow redirect token collects:
- Browser type and version
- Operating system
- Screen resolution
- Installed plugins
- Language settings
- Timezone
- Canvas fingerprint

This data appears in the alert alongside IP address and timestamp.

### Wizard Integration Recommendations

#### Step 3: Token Configuration Enhancement
Add these options when configuring URL-based tokens:

**Token Behavior Selection:**
```
○ Silent Tracking (Web Bug)
  - No redirect, invisible to user
  - Best for: embedded in documents, email images

○ Fast Redirect
  - Immediate redirect, no fingerprinting
  - Best for: links that must work quickly

○ Slow Redirect (Recommended)
  - Collects browser fingerprint before redirect
  - Best for: maximum intelligence on attacker
```

**URL Appearance Customization:**
```
URL Path Style:
  ○ Default (random path)
  ○ Document URL (e.g., /shared/Q4-Report.pdf)
  ○ Admin Panel (e.g., /admin/config.aspx)
  ○ API Endpoint (e.g., /api/v1/users)
  ○ Custom: [________________]
```

**Redirect Destination (for redirect tokens):**
```
Redirect To:
  ○ Google Drive (shared file page)
  ○ SharePoint (document library)
  ○ OneDrive (file viewer)
  ○ Login Page (Microsoft 365)
  ○ Error Page (file not found)
  ○ Custom Landing Page
  ○ Custom URL: [________________]
```

**Browser Scanning:**
```
☑ Enable browser fingerprinting
  Collects browser, OS, plugins, and screen info
  (Only available for Web Bug and Slow Redirect)
```

### URL Style Templates for Wizard

Pre-configured URL path templates by scenario:

| Scenario | Suggested URL Paths |
|----------|---------------------|
| **HR Documents** | `/shared/salaries.xlsx`, `/hr/benefits-2024.pdf` |
| **IT Department** | `/admin/passwords.txt`, `/backup/credentials.zip` |
| **Finance** | `/reports/quarterly-forecast.xlsx`, `/audit/expenses.csv` |
| **Executive** | `/board/strategy-deck.pptx`, `/confidential/merger.pdf` |
| **Developer** | `/api/v1/config`, `/.env`, `/backup/database.sql` |
| **Social/Creator** | `/links/exclusive.html`, `/vip/access.txt` |

### Redirect Destination Templates

Pre-configured redirect URLs by believability:

| Style | Example URLs | Notes |
|-------|--------------|-------|
| **Cloud Storage** | `https://drive.google.com/file/d/...` | Appears as normal file access |
| **Corporate Login** | `https://login.microsoftonline.com/` | Session expired scenario |
| **File Not Found** | Custom 404 page | Attacker thinks link is dead |
| **Access Denied** | Custom 403 page | Suggests file exists but restricted |
| **Rickroll** | YouTube redirect | Obvious detection, humorous |

### Implementation Notes

1. **URL path is client-side only** - The actual token ID is in the hostname/subdomain, so path changes don't require API calls

2. **Redirect URL requires token recreation** - Changing the redirect destination requires creating a new token

3. **Browser scanner adds latency** - Slow redirect tokens may take 2-3 seconds before redirecting

4. **Custom domains require setup** - Using custom domains needs prior configuration in CanaryTokens

---

## URL Shortener Integration

Raw CanaryToken URLs are long and suspicious-looking. URL shorteners can make them appear legitimate and professional.

### Why Use URL Shorteners

**Before (suspicious):**
```
http://canarytokens.com/tags/static/voxr2oprnbs4kp8x1xoj7f89d/contact.php
```

**After (believable):**
```
https://bit.ly/Q4-Budget-Report
https://files.company.com/salary-info
https://link.acme.co/hr-benefits
```

According to security research, "canary tokens hidden behind shortened URLs work almost exactly the same as posting the raw link" and "attract less suspicion than the super-long Canary token URL."

### Cloud-Hosted URL Shorteners with API

| Service | Free Tier | Custom Domain (Free) | API | Custom Slug |
|---------|-----------|---------------------|-----|-------------|
| [**Short.io**](https://short.io/) | 1,000 links | ✅ Yes | ✅ REST | ✅ Yes |
| [**Dub**](https://dub.co) | 25 links | ✅ 3 domains | ✅ REST | ✅ Yes |
| [**Rebrandly**](https://www.rebrandly.com/) | 10 links | ✅ 1 domain | ✅ REST | ✅ Yes |
| [**T.LY**](https://t.ly/) | 10 links | ✅ 1 domain | ✅ REST | ✅ Yes |
| [**Cuttly**](https://cutt.ly/) | Limited | ✅ Paid | ✅ REST | ✅ Yes |
| [**Bitly**](https://bitly.com) | 10 links | ❌ Paid ($35/mo) | ✅ REST | ✅ Yes |
| [**TinyURL**](https://tinyurl.com) | Unlimited | ❌ Paid ($12.99/mo) | ✅ Limited | ✅ Yes |

**Best for CanaryTokens Integration: Short.io**
- 1,000 free branded links/month
- Custom domain included
- REST API for automation
- No infrastructure to manage

### Self-Hosted URL Shorteners (Full Control)

| Project | Language | Database | Docker | API | License |
|---------|----------|----------|--------|-----|---------|
| [**Shlink**](https://shlink.io/) | PHP | MySQL/PostgreSQL/SQLite | ✅ | ✅ REST + CLI | MIT |
| [**YOURLS**](https://yourls.org/) | PHP | MySQL | ✅ | ✅ REST | MIT |
| [**Kutt**](https://kutt.it/) | Node.js | PostgreSQL + Redis | ✅ | ✅ REST | MIT |
| [**Polr**](https://polrproject.org/) | PHP/Lumen | MySQL | ✅ | ✅ REST | GPL |
| [**Dub**](https://github.com/dubinc/dub) | TypeScript | PostgreSQL | ✅ | ✅ REST | AGPL |

**Selected for Implementation: Shlink**
- Full Docker support
- REST API with CORS
- Custom slugs per domain
- QR code generation
- Click analytics
- Multiple domain support

### API Examples

#### Short.io API
```bash
curl -X POST "https://api.short.io/links" \
  -H "Authorization: sk_xxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "link.yourcompany.com",
    "originalURL": "http://canarytokens.com/tags/xxx/file.xlsx",
    "path": "Q4-Budget-Report"
  }'
# Result: https://link.yourcompany.com/Q4-Budget-Report
```

#### Shlink API (Self-Hosted)
```bash
curl -X POST "https://links.yourdomain.com/rest/v3/short-urls" \
  -H "X-Api-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "longUrl": "http://canarytokens.com/tags/xxx/file.xlsx",
    "customSlug": "salary-info",
    "domain": "links.yourdomain.com"
  }'
# Result: https://links.yourdomain.com/salary-info
```

#### YOURLS API
```bash
curl "https://yourls.yourserver.com/yourls-api.php" \
  -d "signature=your-api-key" \
  -d "action=shorturl" \
  -d "url=http://canarytokens.com/tags/xxx/file.xlsx" \
  -d "keyword=admin-passwords"
# Result: https://yourls.yourserver.com/admin-passwords
```

#### Bitly API
```bash
curl -X POST "https://api-ssl.bitly.com/v4/shorten" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "http://canarytokens.com/tags/xxx/file.xlsx",
    "domain": "bit.ly"
  }'
# Result: https://bit.ly/3xYz123
```

### Custom URL Options

#### 1. Custom Slug (Path)
Control the path after the domain:
```
https://bit.ly/Q4-Budget           ← custom slug
https://company.link/salary-2024   ← custom slug
```

#### 2. Custom Domain (Branded)
Use your own domain:
```
https://files.company.com/report   ← your domain
https://docs.acme.co/benefits      ← your domain
```

#### 3. Subdomain Routing
Different subdomains for different scenarios:
```
https://hr.company.link/salaries
https://it.company.link/passwords
https://finance.company.link/budget
```

### Short URL Templates by Scenario

| Scenario | Domain Style | Example Short URLs |
|----------|--------------|-------------------|
| **HR Documents** | `hr.company.link` | `/salaries`, `/benefits-2024`, `/org-chart` |
| **IT Department** | `it.company.link` | `/vpn-config`, `/admin-access`, `/credentials` |
| **Finance** | `finance.company.link` | `/q4-report`, `/budget`, `/projections` |
| **Executive** | `exec.company.link` | `/board-deck`, `/strategy`, `/merger-docs` |
| **Social/Creator** | `link.username.com` | `/exclusive`, `/vip-access`, `/collab` |
| **Generic** | `bit.ly` or `short.io` | `/important-doc`, `/confidential` |

### Deployment Recommendations

#### Option A: Cloud Service (Quick Setup)
**Short.io** - Best free tier with API
- 1,000 links/month free
- Custom domain included
- REST API for automation
- No infrastructure to manage

#### Option B: Self-Hosted (Full Control) ✅ Selected
**Shlink** via Docker - add to existing stack:
```yaml
# Add to docker-compose.yml
shlink:
  image: shlinkio/shlink:stable
  environment:
    DEFAULT_DOMAIN: links.yourdomain.com
    IS_HTTPS_ENABLED: "true"
    DB_DRIVER: postgres
    DB_HOST: postgres
    DB_NAME: shlink
    DB_USER: shlink
    DB_PASSWORD: ${SHLINK_DB_PASSWORD}
  ports:
    - "8080:8080"
```

Benefits of self-hosting:
- Complete data control
- No link limits
- Integrate directly with campaign-api
- Same infrastructure as CanaryTokens
- No third-party dependencies

### Wizard Integration Recommendations

Add to **Step 4: Content Customization**:

```
URL Shortening:
  ○ None (use raw CanaryToken URL)
  ○ Auto-shorten via Short.io
  ○ Auto-shorten via Shlink (self-hosted)
  ○ Manual (I'll shorten myself)

┌─────────────────────────────────────────────┐
│ Short URL Configuration                      │
├─────────────────────────────────────────────┤
│ Domain:  [files.company.com        ▼]       │
│ Path:    [Q4-Budget-Report          ]       │
│                                             │
│ Preview: https://files.company.com/Q4-Budget│
└─────────────────────────────────────────────┘
```

### Security Considerations

1. **Double-edged tool** - Attackers also use URL shorteners to disguise malicious links, so security-aware targets may be suspicious of shortened URLs

2. **Analytics leakage** - Cloud shorteners track clicks; use self-hosted for sensitive operations

3. **Link rot** - Cloud free tiers may expire links; self-hosted ensures permanence

4. **OPSEC** - Custom domains tied to your organization may reveal attribution

---

## Sources

### Wizard UI/UX
- [8 Best Multi-Step Form Examples in 2025 + Best Practices](https://www.webstacks.com/blog/multi-step-form)
- [Wizard UI Pattern: When to Use It and How to Get It Right](https://www.eleken.co/blog-posts/wizard-ui-pattern-explained)
- [Wizard Design Pattern - UX Planet](https://uxplanet.org/wizard-design-pattern-8c86e14f2a38)

### UI Components
- [Interactive Tree View Component with Drag Support for Shadcn/ui](https://next.jqueryscript.net/shadcn-ui/tree-view-drag/)
- [Hierarchical Data Display with Shadcn/ui Tree View](https://next.jqueryscript.net/shadcn-ui/hierarchical-data-tree-view/)
- [File Tree | Magic UI](https://magicui.design/docs/components/file-tree)
- [Tree | Reka UI](https://reka-ui.com/docs/components/tree)

### CanaryTokens Documentation
- [HTTP Canarytoken](https://docs.canarytokens.org/guide/http-token.html)
- [Fast Redirect Canarytoken](https://docs.canarytokens.org/guide/fast-redirect-token.html)
- [Slow Redirect Canarytoken](https://docs.canarytokens.org/guide/slow-redirect-token.html)
- [Factory API Documentation](https://docs.canary.tools/canarytokens/factory.html)
- [Getting Started with Canarytokens](https://docs.canarytokens.org/guide/getting-started.html)
- [How to Create Slow/Fast Redirect Tokens](https://help.canary.tools/hc/en-gb/articles/360021010477-How-do-I-create-a-Slow-Fast-Redirect-Token)
- [Canarytoken Overview and Use Cases](https://help.canary.tools/hc/en-gb/articles/10905485310109-Canarytoken-Overview-and-Use-Cases)
- [Track a Target Using Canary Token Tracking Links](https://null-byte.wonderhowto.com/how-to/track-target-using-canary-token-tracking-links-0192830/)

### URL Shorteners
- [The 7 Best URL Shorteners in 2025 - Zapier](https://zapier.com/blog/best-url-shorteners/)
- [Best URL Shortener APIs - Rebrandly](https://www.rebrandly.com/blog/url-shortener-apis)
- [Short.io - URL Shortener with Custom Domains](https://short.io/)
- [Shlink - Self-Hosted URL Shortener](https://shlink.io/)
- [YOURLS - Your Own URL Shortener](https://yourls.org/)
- [Kutt - Modern URL Shortener](https://kutt.it/)
- [Shlink API Documentation](https://shlink.io/documentation/api-docs/)
- [Bitly API Reference](https://dev.bitly.com/api-reference)
- [Rebrandly Developer API](https://developers.rebrandly.com/)
