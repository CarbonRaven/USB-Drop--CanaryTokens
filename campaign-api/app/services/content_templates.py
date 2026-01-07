"""Content templates for realistic USB drop files."""

from typing import Optional, Union, List
import re
from datetime import datetime
import random

from app.services.url_generator import UrlGenerator, UrlStyle, get_available_styles

# Realistic text content templates with {canary_url} placeholder
TEXT_TEMPLATES = {
    "password_list": {
        "filename": "passwords.txt",
        "content": """=== CONFIDENTIAL - DO NOT SHARE ===
Last Updated: {date}

NETWORK CREDENTIALS
-------------------
Domain Admin: administrator / Winter2024!
VPN Access: vpn_admin / Pr0ject#2024
WiFi (Corporate): CorpNet2024$ecure

SERVER ACCESS
-------------
SQL Server (prod): sa / Sql@dmin2024!
File Server: fileadmin / F1le$hare!
Backup Server: backup_svc / B@ckup2024

CLOUD SERVICES
--------------
AWS Root: admin@company.com / Cl0ud@ccess!
Azure Portal: azure_admin / M$Azure2024
O365 Admin: See {canary_url} for current password

APPLICATION PASSWORDS
---------------------
SAP: sapuser / S@P2024prod
Salesforce: sf_admin / CRM@dmin24
Jira: jira_svc / J1r@Serv1ce

NOTES: Rotate passwords quarterly. Contact IT for emergency access.
For password reset portal: {canary_url}
"""
    },

    "vpn_config": {
        "filename": "vpn-config.txt",
        "content": """# Corporate VPN Configuration
# Updated: {date}
#
# IMPORTANT: Keep this file secure!

[Connection]
Server = vpn.internal.corp.local
Port = 443
Protocol = IKEv2

[Credentials]
Username = remote_user
Password = Vpn@ccess2024!
Certificate = See attachment or download from:
{canary_url}

[Advanced]
SplitTunnel = false
AutoReconnect = true
KillSwitch = enabled

# For VPN issues, contact helpdesk or visit:
# {canary_url}
"""
    },

    "server_inventory": {
        "filename": "server-inventory.txt",
        "content": """SERVER INVENTORY - CONFIDENTIAL
Generated: {date}

PRODUCTION SERVERS
==================
PROD-WEB-01     10.0.1.10    Windows Server 2022    Web Frontend
PROD-WEB-02     10.0.1.11    Windows Server 2022    Web Frontend
PROD-APP-01     10.0.1.20    Windows Server 2022    Application Server
PROD-SQL-01     10.0.1.30    Windows Server 2022    SQL Primary
PROD-SQL-02     10.0.1.31    Windows Server 2022    SQL Secondary

DEVELOPMENT SERVERS
===================
DEV-WEB-01      10.0.2.10    Ubuntu 22.04           Dev Web
DEV-APP-01      10.0.2.20    Ubuntu 22.04           Dev Application
DEV-SQL-01      10.0.2.30    Ubuntu 22.04           Dev Database

MANAGEMENT
==========
MGMT-DC-01      10.0.0.10    Windows Server 2022    Domain Controller
MGMT-DC-02      10.0.0.11    Windows Server 2022    Domain Controller
MGMT-BACKUP     10.0.0.20    Windows Server 2022    Backup Server

For full network diagram, visit: {canary_url}
Admin credentials stored in password vault: {canary_url}
"""
    },

    "meeting_notes": {
        "filename": "meeting-notes.txt",
        "content": """EXECUTIVE MEETING NOTES - CONFIDENTIAL
Date: {date}
Attendees: CEO, CFO, CTO, CISO, Legal

AGENDA
------
1. Q4 Financial Review
2. Security Incident Discussion
3. M&A Update - Project Phoenix
4. 2025 Budget Approval

KEY DISCUSSION POINTS
---------------------
1. Revenue ahead of projections by 12%
2. Security breach in September contained, no customer data exposed
   - Root cause: unpatched VPN appliance
   - Action: Complete vulnerability assessment by EOY

3. Project Phoenix (HIGHLY CONFIDENTIAL)
   - Target company valuation: $45M
   - Due diligence 60% complete
   - Expected close: Q1 2025
   - All documents at: {canary_url}

4. 2025 IT Budget approved: $2.3M
   - Security initiatives: $450K
   - Cloud migration: $800K

ACTION ITEMS
------------
- CTO: Complete security audit by Dec 15
- CFO: Finalize acquisition financing
- CISO: Implement new password policy
- Legal: Review contracts at {canary_url}

NEXT MEETING: First Monday of next month
"""
    },

    "api_keys": {
        "filename": "api-keys.txt",
        "content": """# API Keys and Secrets
# CONFIDENTIAL - DO NOT COMMIT TO VERSION CONTROL
# Last updated: {date}

# ============================================
# PRODUCTION KEYS
# ============================================

# Stripe Payment Processing
STRIPE_SECRET_KEY=sk_live_FAKE_KEY_FOR_USB_DROP_BAIT_1234567890
STRIPE_PUBLISHABLE_KEY=pk_live_FAKE_KEY_FOR_USB_DROP_BAIT_0987654321

# AWS Production
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# SendGrid Email
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Twilio SMS
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database
DATABASE_URL=postgresql://admin:Pr0dDb2024!@db.internal:5432/production

# ============================================
# ADDITIONAL KEYS
# ============================================
# For complete key management, see:
# {canary_url}
#
# Key rotation schedule and procedures:
# {canary_url}
"""
    },

    "network_diagram": {
        "filename": "network-info.txt",
        "content": """NETWORK ARCHITECTURE - INTERNAL USE ONLY
Document Version: 3.2
Last Updated: {date}

OVERVIEW
========
This document contains sensitive network configuration details.
Full network diagram available at: {canary_url}

IP RANGES
=========
Production:     10.0.1.0/24
Development:    10.0.2.0/24
Management:     10.0.0.0/24
DMZ:            172.16.0.0/24
Guest WiFi:     192.168.100.0/24

CRITICAL SYSTEMS
================
Firewall:       10.0.0.1 (Palo Alto PA-3260)
Core Switch:    10.0.0.2 (Cisco Nexus 9300)
Domain Ctrl:    10.0.0.10, 10.0.0.11

VPN CONCENTRATOR
================
External IP:    203.0.113.50
Internal IP:    10.0.0.5
Admin Portal:   {canary_url}

WIRELESS
========
SSID (Corp):    CorpNet-5G
SSID (Guest):   Guest-WiFi
Controller:     10.0.0.30

DOCUMENTATION
=============
Full config backups: {canary_url}
Change management: IT-CHANGE-{year}-XXX
"""
    },

    "employee_list": {
        "filename": "employee-directory.txt",
        "content": """EMPLOYEE DIRECTORY - HR CONFIDENTIAL
Generated: {date}

EXECUTIVE TEAM
==============
John Smith          CEO             john.smith@company.com      Ext 1001
Sarah Johnson       CFO             sarah.j@company.com         Ext 1002
Michael Chen        CTO             m.chen@company.com          Ext 1003
Lisa Williams       CHRO            l.williams@company.com      Ext 1004

IT DEPARTMENT
=============
David Brown         IT Director     d.brown@company.com         Ext 2001
Jennifer Lee        Sys Admin       j.lee@company.com           Ext 2002
Robert Taylor       Network Eng     r.taylor@company.com        Ext 2003
Emily Davis         Security Analyst e.davis@company.com        Ext 2004

FINANCE
=======
James Wilson        Controller      j.wilson@company.com        Ext 3001
Amanda Martinez     AP Manager      a.martinez@company.com      Ext 3002
Christopher Jones   AR Specialist   c.jones@company.com         Ext 3003

EMERGENCY CONTACTS
==================
Security Desk:      Ext 5555
IT Helpdesk:        Ext 4357
HR Hotline:         Ext 4472

For org chart and full directory: {canary_url}
New hire onboarding portal: {canary_url}
"""
    },

    "backup_credentials": {
        "filename": "backup-access.txt",
        "content": """BACKUP SYSTEM CREDENTIALS
========================
CONFIDENTIAL - IT USE ONLY
Updated: {date}

PRIMARY BACKUP (Veeam)
----------------------
Console URL:    https://backup.internal:9443
Username:       backup_admin
Password:       V33@mB@ckup!

Backup Repository:
- Primary: \\\\nas01\\backups
- Secondary: \\\\nas02\\backups-dr
- Cloud: AWS S3 (backup-prod-{year})

DISASTER RECOVERY
-----------------
DR Site:        Equinix DC2
VPN Access:     dr-vpn.company.com
Credentials:    See password vault

Recovery Procedures: {canary_url}
DR Test Schedule: Quarterly

TAPE LIBRARY
------------
Location:       Server Room B, Rack 4
Encryption Key: Stored in vault
Offsite Vendor: Iron Mountain
Pickup:         Weekly (Fridays)

For emergency recovery: {canary_url}
"""
    },

    "wifi_passwords": {
        "filename": "wifi-access.txt",
        "content": """WIRELESS NETWORK ACCESS
=======================
Updated: {date}

CORPORATE NETWORK
-----------------
SSID:       CorpNet-5G
Password:   C0rp0r@te2024WiFi!
Security:   WPA3-Enterprise
Note:       Use domain credentials

GUEST NETWORK
-------------
SSID:       Company-Guest
Password:   Welcome2024!
Portal:     {canary_url}

CONFERENCE ROOMS
----------------
SSID:       ConfRoom-Secure
Password:   M33t1ng2024!
Note:       Video conferencing priority

IOT NETWORK (Restricted)
------------------------
SSID:       IoT-Internal
Password:   Sm@rtDev1ces!
Contact:    IT Security Team

For WiFi issues, visit: {canary_url}
"""
    },

    "project_notes": {
        "filename": "project-confidential.txt",
        "content": """PROJECT PHOENIX - STRICTLY CONFIDENTIAL
========================================
Classification: Board Eyes Only
Date: {date}

EXECUTIVE SUMMARY
-----------------
Proposed acquisition of TechStart Inc.
Estimated value: $45-50M
Strategic rationale: Market expansion + IP acquisition

TIMELINE
--------
Phase 1: Due Diligence (In Progress)
Phase 2: Negotiation (Q1 2025)
Phase 3: Integration (Q2 2025)

KEY CONTACTS
------------
Lead Advisor: Goldman Sachs - Mark Thompson
Legal: Baker McKenzie - Jennifer Walsh
Internal Lead: CFO Sarah Johnson

DOCUMENTS
---------
All confidential documents stored at:
{canary_url}

Letter of Intent: Draft complete
Term Sheet: Under negotiation
Financial Models: {canary_url}

DO NOT DISCUSS THIS PROJECT OUTSIDE APPROVED CHANNELS
For secure file sharing: {canary_url}
"""
    },

    # Personal/Found Drive Scenario
    "resume": {
        "filename": "Resume_John_Smith.txt",
        "content": """JOHN SMITH
==========
Software Engineer | Full Stack Developer

Contact Information
-------------------
Email: john.smith.work@company.com
Phone: (555) 123-4567
LinkedIn: {canary_url}
GitHub: {canary_url}
Portfolio: {canary_url}

Summary
-------
Experienced software engineer with 8+ years of experience in full-stack
development, cloud architecture, and team leadership.

Experience
----------
Senior Software Engineer | TechCorp Inc. | 2020 - Present
- Led migration of legacy systems to cloud infrastructure
- Managed team of 5 developers
- Reduced deployment time by 60%

Software Engineer | StartupXYZ | 2016 - 2020
- Built scalable microservices architecture
- Implemented CI/CD pipelines

Education
---------
BS Computer Science | State University | 2016

Skills
------
Languages: Python, JavaScript, Go, Java
Frameworks: React, Node.js, Django, Spring Boot
Cloud: AWS, GCP, Azure

References available upon request
Contact me at: john.smith.contact@company.com
Or visit my portfolio: {canary_url}
"""
    },

    "personal_contacts": {
        "filename": "important-contacts.txt",
        "content": """MY IMPORTANT CONTACTS
=====================
Last Updated: {date}

FAMILY
------
Mom: (555) 234-5678
Dad: (555) 345-6789
Sister (Emily): (555) 456-7890

EMERGENCY
---------
Doctor: Dr. Sarah Wilson - (555) 111-2222
Dentist: Dr. Michael Chen - (555) 222-3333
Insurance: Policy #A12345 - 1-800-INSURANCE

WORK
----
Boss (David): (555) 777-8888
HR Department: (555) 888-9999
IT Helpdesk: (555) 999-0000

ACCOUNTS
--------
Bank: First National - Account ending 4532
Login portal: {canary_url}

Cloud Storage: {canary_url}
Password Manager: {canary_url}

NOTES
-----
If found, please contact me at:
john.smith.backup@company.com
Or visit: {canary_url}
"""
    },

    "tax_summary": {
        "filename": "tax-info-2024.txt",
        "content": """TAX INFORMATION {year}
======================
PERSONAL - KEEP CONFIDENTIAL

INCOME SUMMARY
--------------
W-2 Wages: $125,000
Freelance Income: $15,000
Investment Dividends: $3,200
Total Gross Income: $143,200

DEDUCTIONS
----------
Mortgage Interest: $12,500
Property Tax: $4,200
Charitable Donations: $2,000
State Income Tax: $6,800
Total Deductions: $25,500

TAX DOCUMENTS
-------------
W-2 from TechCorp: Filed
1099-MISC: Filed
1099-DIV: Filed

ACCOUNTANT
----------
Smith & Associates Tax Services
Contact: Jennifer Smith, CPA
Phone: (555) TAX-HELP
Portal: {canary_url}

Important: All documents uploaded to secure portal
Access tax documents: {canary_url}
"""
    },

    # Training/Compliance Scenario
    "compliance_notice": {
        "filename": "compliance-notice.txt",
        "content": """MANDATORY COMPLIANCE TRAINING NOTICE
=====================================
Date: {date}
Department: All Employees

REQUIRED TRAINING MODULES
-------------------------
All employees must complete the following training by end of quarter:

1. Security Awareness Training (60 minutes)
   Access: {canary_url}

2. Anti-Harassment & Workplace Conduct (45 minutes)
   Access: {canary_url}

3. Data Privacy & GDPR Compliance (30 minutes)
   Access: {canary_url}

4. Code of Conduct Annual Review (20 minutes)
   Access: {canary_url}

COMPLETION REQUIREMENTS
-----------------------
- All modules must be completed with a passing score of 80%
- Deadline: Last day of the current quarter
- Non-completion may affect performance reviews

TRACKING YOUR PROGRESS
----------------------
Login to the training portal to view your progress:
Portal URL: {canary_url}

QUESTIONS?
----------
Contact: compliance@company.com
Training Support: training.support@company.com
Help Portal: {canary_url}

This training is mandatory per company policy HR-2024-15.
"""
    },

    "policy_update": {
        "filename": "policy-update-notice.txt",
        "content": """IMPORTANT POLICY UPDATE NOTICE
==============================
Effective Date: {date}
Policy ID: SEC-{year}-042

TO ALL EMPLOYEES:

The following policies have been updated and require your acknowledgment:

UPDATED POLICIES
----------------
1. Information Security Policy v4.2
   - New requirements for password complexity
   - Updated remote work security guidelines
   - Enhanced data classification rules

2. Acceptable Use Policy v3.1
   - Clarified social media guidelines
   - Updated BYOD requirements
   - New AI tool usage guidelines

3. Incident Response Procedure v2.0
   - Streamlined reporting process
   - New escalation matrix
   - Updated contact information

REQUIRED ACTIONS
----------------
1. Review updated policies at: {canary_url}
2. Complete acknowledgment form: {canary_url}
3. Attend virtual Q&A session (optional): {canary_url}

DEADLINE
--------
All acknowledgments must be submitted within 14 days.

For questions, contact:
- Policy Questions: policy@company.com
- Technical Issues: {canary_url}

Human Resources Department
"""
    },

    # Social Creator Scenario
    "creator_links": {
        "filename": "my-links.txt",
        "content": """MY SOCIAL LINKS
===============
Updated: {date}

MAIN PROFILES
-------------
Subscribe: {canary_url}
Exclusive Content: {canary_url}
Tip Me: {canary_url}

SOCIAL MEDIA
------------
Instagram: @jessica.marie.official
TikTok: @jessicamarie
Twitter/X: @jessmarie_
YouTube: {canary_url}

BUSINESS INQUIRIES
------------------
Email: jessica.business@company.com
Management: {canary_url}
Collaboration Form: {canary_url}

MERCH STORE
-----------
Shop: {canary_url}
Discount Code: JESSICA20

FAN CLUB
--------
Join VIP: {canary_url}
Member Portal: {canary_url}

If you found this drive, please DM me!
@jessica.marie.official

xoxo
"""
    },

    "creator_discount": {
        "filename": "discount-code.txt",
        "content": """EXCLUSIVE FAN DISCOUNT
======================

Thank you for being a supporter!

YOUR SPECIAL CODE: JESSICA50
============================

50% OFF your first month!

HOW TO REDEEM
-------------
1. Visit: {canary_url}
2. Click "Subscribe"
3. Enter code: JESSICA50
4. Enjoy exclusive content!

WHAT YOU GET
------------
- Daily exclusive photos
- Behind the scenes content
- Direct messaging access
- Monthly video calls
- Early access to new content

NEED HELP?
----------
Support: {canary_url}
Email: support@company.com

Code valid until end of {year}
Cannot be combined with other offers

xoxo Jessica
"""
    },

    # Project/Client Scenario
    "project_overview": {
        "filename": "project-overview.txt",
        "content": """PROJECT ALPHA - OVERVIEW
========================
Client: Acme Corporation
Project ID: PRJ-{year}-0042
Status: Active
Last Updated: {date}

PROJECT SUMMARY
---------------
Digital transformation initiative for client's legacy systems.
Total Budget: $1.2M
Timeline: 6 months

KEY MILESTONES
--------------
Phase 1: Discovery & Planning (Complete)
Phase 2: Development (In Progress)
Phase 3: Testing & QA (Upcoming)
Phase 4: Deployment & Training (Upcoming)

PROJECT TEAM
------------
Project Manager: Sarah Johnson
Technical Lead: Michael Chen
Business Analyst: Emily Davis
Lead Developer: Robert Taylor

CLIENT CONTACTS
---------------
Primary: John Smith (CTO)
Secondary: Lisa Williams (IT Director)

RESOURCES
---------
Project Portal: {canary_url}
Shared Documents: {canary_url}
Time Tracking: {canary_url}
Issue Tracker: {canary_url}

NEXT STEPS
----------
1. Complete sprint 4 deliverables
2. Client review meeting (Friday)
3. UAT preparation

All project documents: {canary_url}
"""
    },

    "client_contacts": {
        "filename": "client-contacts.txt",
        "content": """CLIENT CONTACT LIST - CONFIDENTIAL
===================================
Project: Alpha
Client: Acme Corporation
Updated: {date}

EXECUTIVE SPONSORS
------------------
John Smith (CTO)
Email: john.smith@client.com
Phone: (555) 100-2000
Assistant: Mary Johnson - (555) 100-2001

Lisa Williams (IT Director)
Email: lisa.w@client.com
Phone: (555) 100-3000

TECHNICAL TEAM
--------------
David Brown (Lead Architect)
Email: d.brown@client.com
Phone: (555) 100-4000

Jennifer Lee (DBA)
Email: j.lee@client.com
Phone: (555) 100-5000

PROCUREMENT
-----------
Amanda Martinez (Procurement Manager)
Email: a.martinez@client.com
Phone: (555) 100-6000
PO Portal: {canary_url}

MEETING LINKS
-------------
Weekly Status: {canary_url}
Technical Sync: {canary_url}
Executive Review: {canary_url}

DOCUMENT SHARING
----------------
Client Portal: {canary_url}
Secure File Drop: {canary_url}

INTERNAL USE ONLY - DO NOT SHARE WITH UNAUTHORIZED PARTIES
"""
    },

    "statement_of_work": {
        "filename": "sow-summary.txt",
        "content": """STATEMENT OF WORK - SUMMARY
============================
Contract ID: SOW-{year}-ALPHA-001
Client: Acme Corporation
Effective Date: {date}

SCOPE OF SERVICES
-----------------
1. Legacy System Assessment
2. Architecture Design
3. Application Development
4. Data Migration
5. Integration Services
6. User Training
7. Post-Go-Live Support (90 days)

DELIVERABLES
------------
D1: Assessment Report
D2: Technical Architecture Document
D3: Development Sprints (8 total)
D4: Migration Plan & Execution
D5: Training Materials
D6: Go-Live Support

PRICING
-------
Fixed Fee: $1,200,000
Payment Schedule: Monthly milestones
Travel & Expenses: Time & Materials (capped at $50,000)

KEY TERMS
---------
- Change requests require written approval
- Weekly status reports required
- Escalation within 48 hours of issues

DOCUMENT ACCESS
---------------
Full SOW: {canary_url}
Change Request Form: {canary_url}
Invoice Portal: {canary_url}

CONTACTS
--------
Our PM: Sarah Johnson
Client PM: John Smith
Legal: legal@company.com

For contract questions: {canary_url}
"""
    }
}

# Profile templates with pre-configured file structures
# Each profile includes a mix of token types: Word, Excel, PDF, Text, QR Code, Windows Folder
PROFILE_TEMPLATES = {
    "it_department": {
        "name": "IT Department",
        "description": "Technical documents, network configs, and system credentials",
        "folders": ["IT_Resources", "Network", "Backups", "Documentation", "Credentials", "Photos"],
        "files": [
            # Office documents
            {"name": "Network_Diagram_2024.docx", "folder": "Network", "type": "ms_word"},
            {"name": "Server_Inventory.xlsx", "folder": "IT_Resources", "type": "ms_excel"},
            {"name": "Disaster_Recovery_Plan.pdf", "folder": "Documentation", "type": "pdf"},
            {"name": "IT_Security_Policy.pdf", "folder": "Documentation", "type": "pdf"},
            # Text files with embedded URLs
            {"name": "passwords.txt", "folder": "Credentials", "type": "text", "template": "password_list"},
            {"name": "vpn-config.txt", "folder": "Network", "type": "text", "template": "vpn_config"},
            {"name": "server-inventory.txt", "folder": "IT_Resources", "type": "text", "template": "server_inventory"},
            {"name": "backup-access.txt", "folder": "Backups", "type": "text", "template": "backup_credentials"},
            # QR codes
            {"name": "WiFi_Setup_QR.png", "folder": "Network", "type": "qr_code"},
            {"name": "VPN_Portal_QR.png", "folder": "Network", "type": "qr_code"},
            # Windows folder token (triggers when folder is opened)
            {"name": "desktop.ini", "folder": "Credentials", "type": "windows_dir"},
            # Template images
            {"name": "server_room.jpg", "folder": "Photos", "type": "template_image", "source": "server_room.jpg"},
            {"name": "network_diagram.jpg", "folder": "Photos", "type": "template_image", "source": "network_diagram.jpg"},
            {"name": "helpdesk_workspace.jpg", "folder": "Photos", "type": "template_image", "source": "helpdesk_workspace.jpg"},
        ]
    },

    "hr_documents": {
        "name": "HR Documents",
        "description": "Employee records, policies, and onboarding materials",
        "folders": ["HR_Confidential", "Policies", "Onboarding", "Payroll", "Benefits", "Team_Photos"],
        "files": [
            # Office documents
            {"name": "Employee_Handbook_2024.docx", "folder": "Policies", "type": "ms_word"},
            {"name": "Salary_Bands_2024.xlsx", "folder": "Payroll", "type": "ms_excel"},
            {"name": "Benefits_Enrollment_Guide.pdf", "folder": "Benefits", "type": "pdf"},
            {"name": "Onboarding_Checklist.docx", "folder": "Onboarding", "type": "ms_word"},
            {"name": "Performance_Review_Template.xlsx", "folder": "HR_Confidential", "type": "ms_excel"},
            # Text files
            {"name": "employee-directory.txt", "folder": "HR_Confidential", "type": "text", "template": "employee_list"},
            # QR code (e.g., benefits portal, training sign-up)
            {"name": "Benefits_Portal_QR.png", "folder": "Benefits", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Payroll", "type": "windows_dir"},
            # Template images
            {"name": "office_team.jpg", "folder": "Team_Photos", "type": "template_image", "source": "office_team.jpg"},
            {"name": "employee_event.jpg", "folder": "Team_Photos", "type": "template_image", "source": "employee_event.jpg"},
            {"name": "onboarding_desk.jpg", "folder": "Team_Photos", "type": "template_image", "source": "onboarding_desk.jpg"},
        ]
    },

    "finance": {
        "name": "Finance",
        "description": "Financial reports, budgets, and sensitive accounting data",
        "folders": ["Financial_Reports", "Budgets", "Invoices", "Tax_Documents", "Banking", "Photos"],
        "files": [
            # Office documents
            {"name": "Q4_Financial_Report.xlsx", "folder": "Financial_Reports", "type": "ms_excel"},
            {"name": "2025_Budget_Draft.xlsx", "folder": "Budgets", "type": "ms_excel"},
            {"name": "Vendor_Payments.xlsx", "folder": "Invoices", "type": "ms_excel"},
            {"name": "Bank_Account_Details.docx", "folder": "Banking", "type": "ms_word"},
            {"name": "Tax_Filing_2024.pdf", "folder": "Tax_Documents", "type": "pdf"},
            {"name": "Audit_Report_2024.pdf", "folder": "Financial_Reports", "type": "pdf"},
            # Text files
            {"name": "api-keys.txt", "folder": "Banking", "type": "text", "template": "api_keys"},
            {"name": "wire-transfer-details.txt", "folder": "Banking", "type": "text", "template": "password_list"},
            # QR codes
            {"name": "Payment_Portal_QR.png", "folder": "Invoices", "type": "qr_code"},
            {"name": "Expense_Submit_QR.png", "folder": "Invoices", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Banking", "type": "windows_dir"},
            # Template images
            {"name": "financial_charts.jpg", "folder": "Photos", "type": "template_image", "source": "financial_charts.jpg"},
            {"name": "accounting_office.jpg", "folder": "Photos", "type": "template_image", "source": "accounting_office.jpg"},
            {"name": "budget_meeting.jpg", "folder": "Photos", "type": "template_image", "source": "budget_meeting.jpg"},
        ]
    },

    "executive": {
        "name": "Executive",
        "description": "Board materials, M&A documents, and strategic plans",
        "folders": ["Board_Materials", "Strategy", "Confidential", "Legal", "Investor_Relations", "Photos"],
        "files": [
            # Office documents
            {"name": "Board_Presentation_Q4.docx", "folder": "Board_Materials", "type": "ms_word"},
            {"name": "Strategic_Plan_2025.docx", "folder": "Strategy", "type": "ms_word"},
            {"name": "MA_Target_Analysis.xlsx", "folder": "Confidential", "type": "ms_excel"},
            {"name": "Term_Sheet_Draft.pdf", "folder": "Legal", "type": "pdf"},
            {"name": "Investor_Deck_2025.pdf", "folder": "Investor_Relations", "type": "pdf"},
            # Text files
            {"name": "meeting-notes.txt", "folder": "Confidential", "type": "text", "template": "meeting_notes"},
            {"name": "project-confidential.txt", "folder": "Confidential", "type": "text", "template": "project_notes"},
            # QR code (secure document portal)
            {"name": "Board_Portal_QR.png", "folder": "Board_Materials", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Confidential", "type": "windows_dir"},
            # Template images
            {"name": "boardroom.jpg", "folder": "Photos", "type": "template_image", "source": "boardroom.jpg"},
            {"name": "executive_office.jpg", "folder": "Photos", "type": "template_image", "source": "executive_office.jpg"},
            {"name": "strategy_session.jpg", "folder": "Photos", "type": "template_image", "source": "strategy_session.jpg"},
        ]
    },

    "developer": {
        "name": "Developer",
        "description": "Source code configs, API keys, and development resources",
        "folders": ["Source", "Configs", "Documentation", "Keys", "Photos"],
        "files": [
            # Office documents
            {"name": "Architecture_Overview.docx", "folder": "Documentation", "type": "ms_word"},
            {"name": "API_Documentation.pdf", "folder": "Documentation", "type": "pdf"},
            {"name": "Sprint_Planning.xlsx", "folder": "Documentation", "type": "ms_excel"},
            {"name": "Database_Schema.pdf", "folder": "Documentation", "type": "pdf"},
            # Text files (high-value targets for attackers)
            {"name": "api-keys.txt", "folder": "Keys", "type": "text", "template": "api_keys"},
            {"name": ".env.production", "folder": "Configs", "type": "text", "template": "api_keys"},
            {"name": "database-config.txt", "folder": "Configs", "type": "text", "template": "api_keys"},
            {"name": "server-inventory.txt", "folder": "Configs", "type": "text", "template": "server_inventory"},
            # QR codes
            {"name": "Dev_VPN_Setup_QR.png", "folder": "Configs", "type": "qr_code"},
            {"name": "Staging_Access_QR.png", "folder": "Configs", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Keys", "type": "windows_dir"},
            # Template images
            {"name": "dev_workstation.jpg", "folder": "Photos", "type": "template_image", "source": "dev_workstation.jpg"},
            {"name": "code_review.jpg", "folder": "Photos", "type": "template_image", "source": "code_review.jpg"},
            {"name": "tech_meetup.jpg", "folder": "Photos", "type": "template_image", "source": "tech_meetup.jpg"},
        ]
    },

    "network_admin": {
        "name": "Network Admin",
        "description": "Network configurations, WiFi credentials, and infrastructure docs",
        "folders": ["Network_Configs", "Wireless", "Firewall", "VPN", "Credentials", "Photos"],
        "files": [
            # Office documents
            {"name": "Network_Topology.docx", "folder": "Network_Configs", "type": "ms_word"},
            {"name": "Firewall_Rules.xlsx", "folder": "Firewall", "type": "ms_excel"},
            {"name": "Network_Security_Policy.pdf", "folder": "Network_Configs", "type": "pdf"},
            {"name": "VPN_Setup_Guide.pdf", "folder": "VPN", "type": "pdf"},
            # Text files
            {"name": "network-info.txt", "folder": "Network_Configs", "type": "text", "template": "network_diagram"},
            {"name": "wifi-access.txt", "folder": "Wireless", "type": "text", "template": "wifi_passwords"},
            {"name": "vpn-config.txt", "folder": "VPN", "type": "text", "template": "vpn_config"},
            {"name": "router-passwords.txt", "folder": "Credentials", "type": "text", "template": "password_list"},
            # QR codes (WiFi access)
            {"name": "Guest_WiFi_QR.png", "folder": "Wireless", "type": "qr_code"},
            {"name": "Corporate_WiFi_QR.png", "folder": "Wireless", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Credentials", "type": "windows_dir"},
            # Template images
            {"name": "patch_panel.jpg", "folder": "Photos", "type": "template_image", "source": "patch_panel.jpg"},
            {"name": "rack_equipment.jpg", "folder": "Photos", "type": "template_image", "source": "rack_equipment.jpg"},
            {"name": "network_monitoring.jpg", "folder": "Photos", "type": "template_image", "source": "network_monitoring.jpg"},
        ]
    },

    "security_audit": {
        "name": "Security Audit",
        "description": "Penetration test results, vulnerability reports, and security assessments",
        "folders": ["Audit_Reports", "Vulnerabilities", "Credentials", "Evidence", "Tools", "Photos"],
        "files": [
            # Office documents (pentest reports)
            {"name": "Pentest_Report_2024.docx", "folder": "Audit_Reports", "type": "ms_word"},
            {"name": "Vulnerability_Scan.xlsx", "folder": "Vulnerabilities", "type": "ms_excel"},
            {"name": "Executive_Summary.pdf", "folder": "Audit_Reports", "type": "pdf"},
            {"name": "Remediation_Plan.pdf", "folder": "Vulnerabilities", "type": "pdf"},
            {"name": "Technical_Findings.pdf", "folder": "Audit_Reports", "type": "pdf"},
            # Text files (extracted credentials - very tempting)
            {"name": "passwords.txt", "folder": "Credentials", "type": "text", "template": "password_list"},
            {"name": "server-inventory.txt", "folder": "Evidence", "type": "text", "template": "server_inventory"},
            {"name": "network-info.txt", "folder": "Evidence", "type": "text", "template": "network_diagram"},
            {"name": "extracted-hashes.txt", "folder": "Credentials", "type": "text", "template": "password_list"},
            # QR codes
            {"name": "Findings_Portal_QR.png", "folder": "Audit_Reports", "type": "qr_code"},
            {"name": "Remediation_Tracker_QR.png", "folder": "Vulnerabilities", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Credentials", "type": "windows_dir"},
            # Template images
            {"name": "security_dashboard.jpg", "folder": "Photos", "type": "template_image", "source": "security_dashboard.jpg"},
            {"name": "audit_meeting.jpg", "folder": "Photos", "type": "template_image", "source": "audit_meeting.jpg"},
            {"name": "penetration_test.jpg", "folder": "Photos", "type": "template_image", "source": "penetration_test.jpg"},
        ]
    },

    "contractor": {
        "name": "Contractor Access",
        "description": "Temporary access credentials and project documentation",
        "folders": ["Access_Info", "Project_Docs", "Credentials", "Resources", "Photos"],
        "files": [
            # Office documents
            {"name": "Project_Requirements.docx", "folder": "Project_Docs", "type": "ms_word"},
            {"name": "NDA_Signed.pdf", "folder": "Project_Docs", "type": "pdf"},
            {"name": "Timesheet_Template.xlsx", "folder": "Resources", "type": "ms_excel"},
            {"name": "Onboarding_Guide.pdf", "folder": "Project_Docs", "type": "pdf"},
            # Text files
            {"name": "vpn-config.txt", "folder": "Access_Info", "type": "text", "template": "vpn_config"},
            {"name": "wifi-access.txt", "folder": "Access_Info", "type": "text", "template": "wifi_passwords"},
            {"name": "passwords.txt", "folder": "Credentials", "type": "text", "template": "password_list"},
            # QR codes (quick access setup)
            {"name": "VPN_Setup_QR.png", "folder": "Access_Info", "type": "qr_code"},
            {"name": "Timesheet_Portal_QR.png", "folder": "Resources", "type": "qr_code"},
            {"name": "Badge_Request_QR.png", "folder": "Access_Info", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Credentials", "type": "windows_dir"},
            # Template images
            {"name": "temporary_desk.jpg", "folder": "Photos", "type": "template_image", "source": "temporary_desk.jpg"},
            {"name": "project_kickoff.jpg", "folder": "Photos", "type": "template_image", "source": "project_kickoff.jpg"},
            {"name": "remote_work.jpg", "folder": "Photos", "type": "template_image", "source": "remote_work.jpg"},
        ]
    },

    # New scenarios from USB_PAYLOAD_SCENARIOS.md

    "personal_backup": {
        "name": "Personal/Found Drive",
        "description": "Lost personal backup drive with photos, documents, and personal info - appeals to good samaritans",
        "folders": ["Photos", "Documents", "Personal", "Work"],
        "label_suggestions": ["Backup", "My Photos", "Personal"],
        "files": [
            # Office documents (personal documents are tempting)
            {"name": "Resume_John_Smith.docx", "folder": "Documents", "type": "ms_word"},
            {"name": "Tax_Return_2024.pdf", "folder": "Personal", "type": "pdf"},
            {"name": "Bank_Statements.xlsx", "folder": "Personal", "type": "ms_excel"},
            {"name": "Budget_Tracker.xlsx", "folder": "Documents", "type": "ms_excel"},
            {"name": "Important_Passwords.docx", "folder": "Personal", "type": "ms_word"},
            # Text files with embedded links
            {"name": "Resume_John_Smith.txt", "folder": "Documents", "type": "text", "template": "resume"},
            {"name": "important-contacts.txt", "folder": "Personal", "type": "text", "template": "personal_contacts"},
            {"name": "tax-info-2024.txt", "folder": "Personal", "type": "text", "template": "tax_summary"},
            # QR codes
            {"name": "Cloud_Backup_QR.png", "folder": "Documents", "type": "qr_code"},
            {"name": "Contact_Card_QR.png", "folder": "Personal", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Personal", "type": "windows_dir"},
            # Template images - personal vacation/family photos
            {"name": "vacation_beach.jpg", "folder": "Photos", "type": "template_image", "source": "vacation_beach.jpg"},
            {"name": "family_picnic.jpg", "folder": "Photos", "type": "template_image", "source": "family_picnic.jpg"},
            {"name": "pet_photo.jpg", "folder": "Photos", "type": "template_image", "source": "pet_photo.jpg"},
            {"name": "birthday_party.jpg", "folder": "Photos", "type": "template_image", "source": "birthday_party.jpg"},
            {"name": "city_travel.jpg", "folder": "Photos", "type": "template_image", "source": "city_travel.jpg"},
        ],
        "readme": {
            "filename": "PLEASE_READ.txt",
            "content": "If found, please contact me at:\njohn.smith.backup@company.com\n\nThis drive contains important personal files.\nThank you for your honesty!\n\n- John"
        }
    },

    "training_compliance": {
        "name": "Training/Compliance",
        "description": "Mandatory training materials and compliance documents - appeals to all employees",
        "folders": ["Required_Training", "Policy_Updates", "Certifications", "Resources", "Photos"],
        "label_suggestions": ["Mandatory Training", "Compliance 2025", "HR Training"],
        "files": [
            # Office documents
            {"name": "Security_Awareness_Training.docx", "folder": "Required_Training", "type": "ms_word"},
            {"name": "Compliance_Certification.pdf", "folder": "Certifications", "type": "pdf"},
            {"name": "Anti_Harassment_Policy.pdf", "folder": "Policy_Updates", "type": "pdf"},
            {"name": "Training_Completion_Tracker.xlsx", "folder": "Required_Training", "type": "ms_excel"},
            {"name": "Code_of_Conduct_2025.pdf", "folder": "Policy_Updates", "type": "pdf"},
            {"name": "Updated_Employee_Handbook.pdf", "folder": "Policy_Updates", "type": "pdf"},
            # Text files with embedded links
            {"name": "compliance-notice.txt", "folder": "Required_Training", "type": "text", "template": "compliance_notice"},
            {"name": "policy-update-notice.txt", "folder": "Policy_Updates", "type": "text", "template": "policy_update"},
            # QR codes for quick mobile access
            {"name": "Training_Portal_QR.png", "folder": "Required_Training", "type": "qr_code"},
            {"name": "Policy_Portal_QR.png", "folder": "Policy_Updates", "type": "qr_code"},
            {"name": "Certification_QR.png", "folder": "Certifications", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Required_Training", "type": "windows_dir"},
            # Template images
            {"name": "training_room.jpg", "folder": "Photos", "type": "template_image", "source": "training_room.jpg"},
            {"name": "workshop_session.jpg", "folder": "Photos", "type": "template_image", "source": "workshop_session.jpg"},
            {"name": "elearning_laptop.jpg", "folder": "Photos", "type": "template_image", "source": "elearning_laptop.jpg"},
            {"name": "certificate.jpg", "folder": "Photos", "type": "template_image", "source": "certificate.jpg"},
        ],
        "readme": {
            "filename": "IMPORTANT.txt",
            "content": "MANDATORY TRAINING MATERIALS\n\nComplete all training by end of quarter.\nAccess portal: https://training.company.com\n\nOr scan QR codes in documents for mobile access.\n\nQuestions? Contact compliance@company.com"
        }
    },

    "social_creator": {
        "name": "Social Creator",
        "description": "Content creator backup drive with photos and exclusive content links - high engagement scenario",
        "folders": ["Photos", "My_Links", "Private", "Videos"],
        "label_suggestions": ["Backup", "My Photos", ""],
        "files": [
            # Pre-generated template images (lifestyle photos)
            {"name": "coffee_lifestyle.jpg", "folder": "Photos", "type": "template_image", "source": "coffee_lifestyle.jpg"},
            {"name": "fitness_gym.jpg", "folder": "Photos", "type": "template_image", "source": "fitness_gym.jpg"},
            {"name": "beach_casual.jpg", "folder": "Photos", "type": "template_image", "source": "beach_casual.jpg"},
            {"name": "home_office.jpg", "folder": "Photos", "type": "template_image", "source": "home_office.jpg"},
            {"name": "urban_style.jpg", "folder": "Photos", "type": "template_image", "source": "urban_style.jpg"},
            # HTML beacons styled as profile pages
            {"name": "My_Profile.html", "folder": "My_Links", "type": "html_beacon"},
            {"name": "Click_to_Watch.html", "folder": "Videos", "type": "html_beacon"},
            # Office documents with embedded links and QR codes
            {"name": "Exclusive_Content_Access.docx", "folder": "Private", "type": "ms_word"},
            {"name": "Fan_Discount_Code.pdf", "folder": "Private", "type": "pdf"},
            {"name": "Subscriber_List.xlsx", "folder": "Private", "type": "ms_excel"},
            # Text files with links
            {"name": "my-links.txt", "folder": "My_Links", "type": "text", "template": "creator_links"},
            {"name": "discount-code.txt", "folder": "Private", "type": "text", "template": "creator_discount"},
            # QR codes
            {"name": "Subscribe_QR.png", "folder": "My_Links", "type": "qr_code"},
            {"name": "VIP_Access_QR.png", "folder": "Private", "type": "qr_code"},
            # Windows folder tokens
            {"name": "desktop.ini", "folder": "Photos", "type": "windows_dir"},
            {"name": "desktop.ini", "folder": "Private", "type": "windows_dir"},
        ],
        "readme": {
            "filename": "About_Me.txt",
            "content": "Hey! This is my backup drive. If found please DM me!\n\nInstagram: @jessica.marie.official\nOr email: jessica.content.backup@company.com\n\nxoxo"
        }
    },

    "project_client": {
        "name": "Project/Client",
        "description": "Client project materials with contracts, contacts, and sensitive business data",
        "folders": ["Project_Alpha", "Client_Data", "Contracts", "Presentations", "Photos"],
        "label_suggestions": ["Project Alpha - Client Materials", "Client Documents", "Project Files"],
        "files": [
            # Office documents
            {"name": "Statement_of_Work.docx", "folder": "Contracts", "type": "ms_word"},
            {"name": "Project_Budget.xlsx", "folder": "Project_Alpha", "type": "ms_excel"},
            {"name": "Client_Requirements.pdf", "folder": "Project_Alpha", "type": "pdf"},
            {"name": "Customer_List.xlsx", "folder": "Client_Data", "type": "ms_excel"},
            {"name": "Contract_Draft.docx", "folder": "Contracts", "type": "ms_word"},
            {"name": "Pricing_Calculator.xlsx", "folder": "Client_Data", "type": "ms_excel"},
            {"name": "Client_Pitch_Deck.pdf", "folder": "Presentations", "type": "pdf"},
            {"name": "NDA_Signed.pdf", "folder": "Contracts", "type": "pdf"},
            # Text files with embedded links
            {"name": "project-overview.txt", "folder": "Project_Alpha", "type": "text", "template": "project_overview"},
            {"name": "client-contacts.txt", "folder": "Client_Data", "type": "text", "template": "client_contacts"},
            {"name": "sow-summary.txt", "folder": "Contracts", "type": "text", "template": "statement_of_work"},
            # QR codes
            {"name": "Project_Portal_QR.png", "folder": "Project_Alpha", "type": "qr_code"},
            {"name": "Client_Portal_QR.png", "folder": "Client_Data", "type": "qr_code"},
            {"name": "Document_Share_QR.png", "folder": "Contracts", "type": "qr_code"},
            # Windows folder token
            {"name": "desktop.ini", "folder": "Client_Data", "type": "windows_dir"},
            # Template images
            {"name": "project_whiteboard.jpg", "folder": "Photos", "type": "template_image", "source": "project_whiteboard.jpg"},
            {"name": "client_meeting.jpg", "folder": "Photos", "type": "template_image", "source": "client_meeting.jpg"},
            {"name": "kanban_board.jpg", "folder": "Photos", "type": "template_image", "source": "kanban_board.jpg"},
            {"name": "team_collaboration.jpg", "folder": "Photos", "type": "template_image", "source": "team_collaboration.jpg"},
        ],
        "readme": {
            "filename": "README.txt",
            "content": "PROJECT ALPHA - CONFIDENTIAL\n\nThis drive contains client materials.\nIf found, please return to Project Management.\n\nContact: pm@company.com\nProject Portal: https://projects.company.com/alpha"
        }
    }
}


# AI Image Generation Prompts for Social Creator scenario
# These are safe, appropriate prompts for DALL-E to generate profile-style photos
AI_IMAGE_PROMPTS = {
    "creator_headshot": {
        "prompt": "Professional headshot portrait of a young woman in her mid-20s, natural lighting, neutral gray background, casual professional attire like a blazer over t-shirt, warm friendly smile, high quality photography style",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_coffee_shop": {
        "prompt": "Lifestyle photo of a young woman sitting at a modern coffee shop, casual clothing, holding a latte with latte art, natural daylight through large windows, cozy atmosphere, candid photography style",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_outdoor_casual": {
        "prompt": "Casual outdoor photo of a young woman in a park setting, wearing athletic wear like yoga pants and hoodie, sunny day, trees in background, natural candid pose, lifestyle photography",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_home_casual": {
        "prompt": "Casual home photo of a young woman in comfortable home attire, living room setting with natural lighting from window, relaxed pose, warm and inviting atmosphere, lifestyle photography",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_beach": {
        "prompt": "Beach lifestyle photo of a young woman wearing a casual summer dress and sunhat, ocean and sandy beach in background, golden hour warm lighting, vacation photography style",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_gym": {
        "prompt": "Fitness lifestyle photo of a young woman at a modern gym, wearing athletic wear, holding water bottle, gym equipment in background, energetic and healthy vibe, fitness photography",
        "size": "1024x1024",
        "style": "natural"
    },
    "creator_working": {
        "prompt": "Work from home photo of a young woman at a desk with laptop, casual business attire, home office setting, focused expression, natural window lighting, lifestyle photography",
        "size": "1024x1024",
        "style": "natural"
    }
}


# Pre-generated template images - stored in /app/uploads/template_images/
TEMPLATE_IMAGES = {
    "it_department": [
        {"filename": "server_room.jpg", "description": "Data center server room with racks"},
        {"filename": "network_diagram.jpg", "description": "Whiteboard with network topology"},
        {"filename": "helpdesk_workspace.jpg", "description": "IT helpdesk workstation"},
    ],
    "hr_documents": [
        {"filename": "office_team.jpg", "description": "Team meeting in modern office"},
        {"filename": "employee_event.jpg", "description": "Employee appreciation event"},
        {"filename": "onboarding_desk.jpg", "description": "New employee welcome setup"},
    ],
    "finance": [
        {"filename": "financial_charts.jpg", "description": "Financial charts on monitor"},
        {"filename": "accounting_office.jpg", "description": "Accounting workspace"},
        {"filename": "budget_meeting.jpg", "description": "Budget review meeting"},
    ],
    "executive": [
        {"filename": "boardroom.jpg", "description": "Corporate boardroom"},
        {"filename": "executive_office.jpg", "description": "Executive corner office"},
        {"filename": "strategy_session.jpg", "description": "Strategic planning at whiteboard"},
    ],
    "personal_backup": [
        {"filename": "vacation_beach.jpg", "description": "Beach sunset vacation photo"},
        {"filename": "family_picnic.jpg", "description": "Family picnic in park"},
        {"filename": "pet_photo.jpg", "description": "Pet dog portrait"},
        {"filename": "birthday_party.jpg", "description": "Birthday celebration"},
        {"filename": "city_travel.jpg", "description": "City skyline travel photo"},
    ],
    "training_compliance": [
        {"filename": "training_room.jpg", "description": "Corporate training room"},
        {"filename": "workshop_session.jpg", "description": "Interactive workshop"},
        {"filename": "elearning_laptop.jpg", "description": "Online training on laptop"},
        {"filename": "certificate.jpg", "description": "Completion certificate"},
    ],
    "social_creator": [
        {"filename": "coffee_lifestyle.jpg", "description": "Coffee shop lifestyle photo"},
        {"filename": "fitness_gym.jpg", "description": "Gym fitness photo"},
        {"filename": "beach_casual.jpg", "description": "Beach casual photo"},
        {"filename": "home_office.jpg", "description": "Home office work photo"},
        {"filename": "urban_style.jpg", "description": "Urban street style photo"},
    ],
    "project_client": [
        {"filename": "project_whiteboard.jpg", "description": "Project planning whiteboard"},
        {"filename": "client_meeting.jpg", "description": "Client meeting room"},
        {"filename": "kanban_board.jpg", "description": "Kanban project board"},
        {"filename": "team_collaboration.jpg", "description": "Team collaboration space"},
    ],
    "developer": [
        {"filename": "dev_workstation.jpg", "description": "Developer workstation"},
        {"filename": "code_review.jpg", "description": "Pair programming session"},
        {"filename": "tech_meetup.jpg", "description": "Tech conference/meetup"},
    ],
    "network_admin": [
        {"filename": "patch_panel.jpg", "description": "Network patch panel"},
        {"filename": "rack_equipment.jpg", "description": "Network equipment rack"},
        {"filename": "network_monitoring.jpg", "description": "NOC monitoring screens"},
    ],
    "security_audit": [
        {"filename": "security_dashboard.jpg", "description": "Security operations dashboard"},
        {"filename": "audit_meeting.jpg", "description": "Security audit meeting"},
        {"filename": "penetration_test.jpg", "description": "Penetration testing setup"},
    ],
    "contractor": [
        {"filename": "temporary_desk.jpg", "description": "Contractor hot desk"},
        {"filename": "project_kickoff.jpg", "description": "Project kickoff meeting"},
        {"filename": "remote_work.jpg", "description": "Remote work from home"},
    ],
}


def get_template_images(template_id: str) -> list:
    """Get the pre-generated images for a template."""
    return TEMPLATE_IMAGES.get(template_id, [])


def list_all_template_images() -> dict:
    """List all available template images."""
    return {
        template_id: [img["filename"] for img in images]
        for template_id, images in TEMPLATE_IMAGES.items()
    }


def generate_text_content(
    template_name: str,
    canary_urls: Union[str, List[str]],
    styled_domain: Optional[str] = None,
    url_style: Optional[str] = None,
    scenario_type: Optional[str] = None,
) -> Optional[str]:
    """
    Generate text file content with embedded canary URLs.

    Args:
        template_name: Name of the text template to use
        canary_urls: A single URL string or list of URLs (one per placeholder)
        styled_domain: Optional custom domain for believable URLs
        url_style: Optional URL style (sharepoint, onedrive, google_drive, etc.)
        scenario_type: Optional scenario type to auto-select URL style

    Returns:
        Generated text content with URLs embedded
    """
    template = TEXT_TEMPLATES.get(template_name)
    if not template:
        return None

    # Normalize to list
    if isinstance(canary_urls, str):
        url_list = [canary_urls]
    else:
        url_list = list(canary_urls)

    # Process URLs through styled domain if configured
    display_urls = []
    for url in url_list:
        if styled_domain:
            # Use the URL generator for a more believable URL
            if url_style:
                style = UrlStyle(url_style)
            elif scenario_type:
                style = UrlGenerator.get_style_for_scenario(scenario_type)
            else:
                style = UrlStyle.GENERIC

            # Generate a styled path using the canary URL as the token ID
            display_url = UrlGenerator.generate_full_url(
                base_domain=styled_domain,
                style=style,
                token_id=url,  # Hash the URL to create consistent short IDs
                use_https=True
            )
            display_urls.append(display_url)
        else:
            display_urls.append(url)

    now = datetime.now()
    template_content = template["content"]

    # Replace each {canary_url} with a unique URL from the list
    url_index = [0]  # Use list to allow modification in closure

    def replace_url(match):
        """Replace each {canary_url} with the next URL in the list."""
        url = display_urls[url_index[0] % len(display_urls)]
        url_index[0] += 1
        return url

    # Do all replacements with regex to handle templates with literal braces
    content = re.sub(r'\{canary_url\}', replace_url, template_content)
    content = re.sub(r'\{date\}', now.strftime("%B %d, %Y"), content)
    content = re.sub(r'\{year\}', now.strftime("%Y"), content)

    return content


def get_template_filename(template_name: str) -> Optional[str]:
    """Get the default filename for a template."""
    template = TEXT_TEMPLATES.get(template_name)
    return template["filename"] if template else None


def get_profile_template(template_name: str) -> Optional[dict]:
    """Get a profile template by name."""
    return PROFILE_TEMPLATES.get(template_name)


def list_profile_templates() -> list:
    """List all available profile templates."""
    return [
        {
            "id": key,
            "name": template["name"],
            "description": template["description"],
            "file_count": len(template["files"]),
            "folder_count": len(template["folders"]),
        }
        for key, template in PROFILE_TEMPLATES.items()
    ]


def list_text_templates() -> list:
    """List all available text templates."""
    return [
        {
            "id": key,
            "filename": template["filename"],
        }
        for key, template in TEXT_TEMPLATES.items()
    ]


def get_ai_image_prompt(prompt_id: str) -> Optional[dict]:
    """Get an AI image prompt configuration by ID."""
    return AI_IMAGE_PROMPTS.get(prompt_id)


def list_ai_image_prompts() -> list:
    """List all available AI image prompts."""
    return [
        {
            "id": key,
            "prompt": config["prompt"][:100] + "..." if len(config["prompt"]) > 100 else config["prompt"],
            "size": config["size"],
            "style": config["style"],
        }
        for key, config in AI_IMAGE_PROMPTS.items()
    ]


def get_profile_files_with_ai_images(template_name: str) -> list:
    """Get list of files that require AI image generation for a template."""
    template = PROFILE_TEMPLATES.get(template_name)
    if not template:
        return []

    return [
        {
            "name": f["name"],
            "folder": f["folder"],
            "prompt": f.get("prompt", ""),
        }
        for f in template.get("files", [])
        if f.get("type") == "ai_image"
    ]


def list_url_styles() -> list:
    """List all available URL styles for believable link generation."""
    return get_available_styles()


def generate_styled_url(
    token_id: str,
    domain: str,
    style: str = "generic",
    filename: Optional[str] = None,
) -> str:
    """
    Generate a believable styled URL for a token.

    Args:
        token_id: The unique token identifier (or canary URL to hash)
        domain: The domain to use (e.g., 'docs.internal-corp.com')
        style: URL style - sharepoint, onedrive, google_drive, corporate_portal,
               dropbox, box, or generic
        filename: Optional filename to include in the path

    Returns:
        Full URL with believable path

    Example:
        >>> generate_styled_url("abc123", "docs.company.com", "sharepoint")
        'https://docs.company.com/_layouts/15/guestaccess.aspx?docid=x8kL2nMpQr'
    """
    try:
        url_style = UrlStyle(style)
    except ValueError:
        url_style = UrlStyle.GENERIC

    return UrlGenerator.generate_full_url(
        base_domain=domain,
        style=url_style,
        token_id=token_id,
        filename=filename,
        use_https=True
    )


def get_recommended_url_style(scenario_type: str) -> str:
    """
    Get the recommended URL style for a scenario type.

    Args:
        scenario_type: The scenario type (e.g., 'corporate', 'personal')

    Returns:
        Recommended URL style name
    """
    return UrlGenerator.get_style_for_scenario(scenario_type).value
