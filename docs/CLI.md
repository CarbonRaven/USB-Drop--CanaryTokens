# USB Drop CLI - User Guide

Command-line interface for preparing and deploying USB drives in penetration testing campaigns.

## Installation

### From Source (Recommended)

```bash
cd usb-drop-cli
pip install -e .
```

### Dependencies

The CLI requires Python 3.9+ and installs these packages:
- `click` - Command-line interface framework
- `questionary` - Interactive prompts
- `rich` - Formatted terminal output (tables, colors)
- `requests` - HTTP client for API communication

## Configuration

Before using the CLI, configure your API connection:

```bash
# Set the API server URL
usb-drop config set-api https://api.yourdomain.com

# Set your API key (generate from web interface Settings > API Keys)
usb-drop config set-key your-api-key-here

# Optionally set a default campaign
usb-drop config set-campaign campaign-uuid

# Verify configuration
usb-drop config show
```

### Configuration File

Configuration is stored in `~/.usb-drop/config.yaml`:

```yaml
api_url: https://api.yourdomain.com
api_key: your-api-key-here
default_campaign: null  # or campaign UUID
```

### Environment Variables

You can also configure the CLI using environment variables (override config file):

```bash
export USB_DROP_API_URL=https://api.yourdomain.com
export USB_DROP_API_KEY=your-api-key
```

## Commands

### Version

```bash
# Show CLI version
usb-drop --version
```

### Configuration

```bash
# Set API URL
usb-drop config set-api <url>

# Set API key
usb-drop config set-key <key>

# Set default campaign
usb-drop config set-campaign <campaign-id>

# Show current configuration
usb-drop config show
```

### Campaigns

```bash
# List all campaigns
usb-drop list-campaigns
```

**Output columns:** ID (truncated), Name, Client, Status, Drives

### Profiles

```bash
# List available USB profiles
usb-drop list-profiles
```

**Output columns:** ID (truncated), Name, Scenario, Token Types

### Drives

```bash
# List all drives
usb-drop list-drives

# Filter by campaign
usb-drop list-drives --campaign <campaign-id>

# Filter by status
usb-drop list-drives --status deployed
```

**Output columns:** Code, Label, Status, Tokens, Triggers

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--campaign` | `-c` | Filter by campaign ID |
| `--status` | `-s` | Filter by status |

### Drive Status Values

| Status | Description |
|--------|-------------|
| `created` | Drive record exists, no tokens generated yet |
| `prepared` | Tokens generated, ready for download |
| `deployed` | Physically placed in the field |
| `triggered` | At least one token has been accessed |
| `recovered` | Drive has been collected |

### Preparing a Drive

```bash
# Interactive mode (recommended for first-time use)
usb-drop prepare --interactive

# Direct mode with all options
usb-drop prepare --campaign <campaign-id> --profile <profile-id> --label "HR Payroll Q4"

# Using default campaign
usb-drop prepare --profile <profile-id> --label "IT Support"
```

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--campaign` | `-c` | Campaign ID (uses default if not specified) |
| `--profile` | `-p` | Profile ID (required in direct mode) |
| `--label` | `-l` | Drive label for identification |
| `--interactive` | `-i` | Enable interactive prompts |

The prepare command:
1. Creates a new drive record in the database
2. Generates tokens via CanaryTokens API
3. Returns the unique drive code (e.g., `USB-A1B2C3`)
4. Shows list of created tokens

### Downloading Drive Files

```bash
# Download as ZIP file (default filename: drive-<id>.zip)
usb-drop download <drive-id>

# Save to specific location
usb-drop download <drive-id> --output /path/to/file.zip

# Write directly to USB drive
usb-drop download <drive-id> --usb

# Clear USB before writing
usb-drop download <drive-id> --usb --clear
```

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--output` | `-o` | Output path for ZIP file |
| `--usb` | `-u` | Write directly to USB drive |
| `--clear` | | Clear USB contents before writing |

### Deploying a Drive

Record the physical deployment location:

```bash
# With coordinates and details
usb-drop deploy <drive-id> --lat 37.7749 --lon -122.4194 --location "Building A lobby" --by "John Smith"

# Interactive mode
usb-drop deploy <drive-id> --interactive
```

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--lat` | | Latitude coordinate (required) |
| `--lon` | | Longitude coordinate (required) |
| `--location` | `-l` | Location description |
| `--by` | `-b` | Deployed by (operator name) |
| `--interactive` | `-i` | Enable interactive prompts |

### Checking Drive Status

```bash
# Get status by drive code
usb-drop status USB-A1B2C3
```

**Output includes:**
- Drive code and label
- Current status
- Creation and deployment timestamps
- Token count and types
- Trigger count per token

### Viewing Alerts

```bash
# Recent alerts (last 24 hours)
usb-drop alerts

# Custom time range
usb-drop alerts --hours 168  # Last 7 days
usb-drop alerts --hours 1    # Last hour
```

**Output columns:** Time, Drive, Token, IP, Location

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--hours` | `-h` | Hours to look back (default: 24) |

## Workflow Example

### Complete USB Preparation Workflow

```bash
# 1. List available campaigns
usb-drop list-campaigns

# 2. List available profiles
usb-drop list-profiles

# 3. Prepare a new drive (interactive)
usb-drop prepare --interactive
# Select campaign: "Client Assessment"
# Select profile: "HR Payroll"
# Enter label: "Payroll Reports"
# Output: Drive created: USB-A1B2C3

# 4. Download to USB drive
usb-drop download <drive-id> --usb --clear
# Select USB drive: /Volumes/UNTITLED
# Files written successfully

# 5. Record deployment
usb-drop deploy <drive-id> --interactive
# Enter latitude: 37.7749
# Enter longitude: -122.4194
# Enter location: Building A lobby, near elevator
# Enter deployed by: John Smith
# Deployment recorded!

# 6. Monitor for triggers
usb-drop alerts --hours 1
```

### Batch Operations

For preparing multiple drives:

```bash
#!/bin/bash

CAMPAIGN="your-campaign-id"
PROFILE="your-profile-id"

for i in {1..10}; do
    usb-drop prepare \
        --campaign $CAMPAIGN \
        --profile $PROFILE \
        --label "Drive $i"
done
```

### Quick Status Check Script

```bash
#!/bin/bash

# Check all deployed drives for triggers
for code in USB-A1B2C3 USB-D4E5F6 USB-G7H8I9; do
    echo "=== $code ==="
    usb-drop status $code
    echo
done
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (API error, configuration missing, invalid input) |

## Troubleshooting

### Connection Errors

```bash
# Check configuration
usb-drop config show

# Test API connectivity
curl -H "X-API-Key: your-key" https://api.yourdomain.com/api/auth/me
```

### "CLI not configured" Error

Run the configuration commands:

```bash
usb-drop config set-api https://api.yourdomain.com
usb-drop config set-key your-api-key
```

### USB Drive Not Detected

The CLI looks for USB drives in:
- **macOS**: `/Volumes/`
- **Linux**: `/media/` and `/mnt/`
- **Windows**: Drive letters other than C:

Ensure your USB drive is properly mounted and accessible.

### Permission Errors

```bash
# macOS/Linux: Run with sudo if needed for USB access
sudo usb-drop download <drive-id> --usb
```

### API Key Invalid

1. Verify your API key in the web interface (Settings > API Keys)
2. Check if the key has been revoked or expired
3. Generate a new key if needed

### Drive Download Returns Empty ZIP

```bash
# Check drive status - must be "prepared"
usb-drop status <drive-code>

# If status is "created", prepare it first
usb-drop prepare --campaign <id> --profile <id>
```

## Output Formats

The CLI uses Rich for formatted output with colors and tables. Status indicators:

| Color | Meaning |
|-------|---------|
| Green | Active, deployed, success |
| Blue | Prepared, completed |
| Yellow | Archived, recovered, warning |
| Red | Triggered, error |
| Dim | Created, draft, waiting |

For machine-readable output, use the API directly with JSON responses.

## API Client Methods

The CLI exposes common operations. Additional API methods available in `api_client.py` for scripting:

| Method | Description |
|--------|-------------|
| `get_campaign(id)` | Get single campaign details |
| `get_campaign_stats(id)` | Campaign statistics |
| `preview_profile(id)` | Preview profile file structure |
| `get_campaign_report(id)` | Generate campaign report |
| `export_campaign_csv(id)` | Export campaign data as CSV |

Example usage in Python:

```python
from usb_drop.api_client import client

# Get campaign report
report = client.get_campaign_report("campaign-uuid")
print(f"Total triggers: {report['total_triggers']}")

# Export to CSV
response = client.export_campaign_csv("campaign-uuid")
with open("report.csv", "wb") as f:
    f.write(response.content)
```
