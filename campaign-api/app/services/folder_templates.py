"""Folder structure templates for realistic USB drives."""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class JunkFile:
    """A junk file to add realism to USB drives."""
    path: str
    content: str
    is_binary: bool = False


@dataclass
class FolderTemplate:
    """Template for folder structure."""
    name: str
    description: str
    folders: List[str]
    junk_files: List[JunkFile] = field(default_factory=list)
    system_files: bool = True  # Include .DS_Store, Thumbs.db


class FolderTemplates:
    """Pre-defined folder structure templates for realistic USB drives."""

    # =========================================================================
    # Personal/Found Drive Scenario
    # =========================================================================
    PERSONAL = FolderTemplate(
        name="personal",
        description="Personal backup drive with photos, documents",
        folders=[
            "DCIM",
            "DCIM/100APPLE",
            "DCIM/101APPLE",
            "Documents",
            "Documents/Personal",
            "Documents/Work",
            "Photos",
            "Photos/Vacation 2024",
            "Photos/Family",
            "Music",
            "Downloads",
            "Backups",
        ],
        junk_files=[
            JunkFile("notes.txt", "Call dentist Monday\nPick up prescription\nGroceries - milk, bread, eggs"),
            JunkFile("shopping_list.txt", "Target:\n- Paper towels\n- Laundry detergent\n- Trash bags\n\nCostco:\n- Water bottles\n- Snacks"),
            JunkFile("Documents/Personal/todo.txt", "1. Pay rent (due 1st)\n2. Schedule oil change\n3. Call mom\n4. Renew gym membership"),
            JunkFile("Documents/Personal/passwords_old.txt", "DO NOT USE - old passwords\n\nBank: ***deleted***\nEmail: ***deleted***\n\nMoved to password manager"),
            JunkFile("Downloads/readme.txt", "Downloaded files - clean up monthly"),
            JunkFile("Photos/Vacation 2024/.metadata", "Album: Summer Vacation 2024\nLocation: Various"),
        ]
    )

    # =========================================================================
    # Social Creator Scenario
    # =========================================================================
    SOCIAL_CREATOR = FolderTemplate(
        name="social_creator",
        description="Content creator backup with photos and links",
        folders=[
            "Content",
            "Content/Photos",
            "Content/Videos",
            "Content/Drafts",
            "Collabs",
            "Analytics",
            "Contracts",
            "My_Links",
            "Private",
        ],
        junk_files=[
            JunkFile("Content/schedule.txt", "POSTING SCHEDULE\n================\nMon/Wed/Fri: Instagram\nTue/Thu: TikTok\nSat: YouTube\nSun: Rest"),
            JunkFile("Content/ideas.txt", "Content Ideas:\n- Day in my life\n- Get ready with me\n- Q&A with fans\n- Behind the scenes\n- Collab with @sarah"),
            JunkFile("Analytics/notes.txt", "Best performing:\n- Lifestyle content\n- Morning routines\n- Travel vlogs\n\nPost between 6-8pm for best engagement"),
            JunkFile("Collabs/pending.txt", "Waiting to hear back:\n- Brand X (skincare)\n- Brand Y (fashion)\n- Brand Z (fitness app)"),
        ]
    )

    # =========================================================================
    # Corporate/HR Scenario
    # =========================================================================
    CORPORATE = FolderTemplate(
        name="corporate",
        description="Corporate documents and reports",
        folders=[
            "Documents",
            "Documents/Archive",
            "Documents/2024",
            "Documents/2025",
            "Reports",
            "Reports/Q4_2024",
            "Presentations",
            "Templates",
            "Data",
            "Meeting_Notes",
        ],
        junk_files=[
            JunkFile("notes.txt", "Action Items:\n- Follow up on Q4 projections\n- Schedule team sync\n- Review budget proposal"),
            JunkFile("Documents/Archive/old_notes.txt", "Legacy content - do not delete\nMigrated to SharePoint 2023"),
            JunkFile("Meeting_Notes/weekly_sync.txt", "Weekly Team Sync\n================\nTime: Tuesday 10am\nLocation: Conf Room B\n\nStanding Agenda:\n1. Updates\n2. Blockers\n3. Action items"),
            JunkFile("Templates/readme.txt", "Approved templates for company use\nLast updated: 2024-11"),
        ]
    )

    # =========================================================================
    # HR Documents Scenario
    # =========================================================================
    HR_DOCUMENTS = FolderTemplate(
        name="hr_documents",
        description="HR policies, employee documents",
        folders=[
            "Policies",
            "Policies/2024",
            "Policies/2025",
            "Onboarding",
            "Benefits",
            "Training",
            "Forms",
            "Archive",
        ],
        junk_files=[
            JunkFile("readme.txt", "HR DOCUMENTS\n============\nConfidential - Internal Use Only\n\nFor questions contact: hr@company.com"),
            JunkFile("Policies/update_log.txt", "Policy Updates 2024:\n- Jan: Remote work policy revised\n- Mar: PTO policy updated\n- Sep: Security awareness added"),
            JunkFile("Onboarding/checklist.txt", "New Hire Checklist:\n[ ] Badge request\n[ ] IT setup\n[ ] Benefits enrollment\n[ ] Direct deposit\n[ ] Emergency contact"),
            JunkFile("Forms/index.txt", "Available Forms:\n1. PTO Request\n2. Expense Report\n3. Travel Authorization\n4. Equipment Request"),
        ]
    )

    # =========================================================================
    # Finance Scenario
    # =========================================================================
    FINANCE = FolderTemplate(
        name="finance",
        description="Financial documents and reports",
        folders=[
            "Financial_Reports",
            "Financial_Reports/2024",
            "Budgets",
            "Invoices",
            "Tax_Documents",
            "Audit",
            "Banking",
            "Archive",
        ],
        junk_files=[
            JunkFile("readme.txt", "FINANCE DEPARTMENT\n==================\nConfidential - Authorized Personnel Only"),
            JunkFile("Financial_Reports/schedule.txt", "Reporting Schedule:\n- Monthly close: 5th business day\n- Quarterly reports: 15th of following month\n- Annual audit: February"),
            JunkFile("Archive/migration_note.txt", "Historical data prior to 2020 archived to cold storage\nContact IT for retrieval requests"),
        ]
    )

    # =========================================================================
    # Executive Scenario
    # =========================================================================
    EXECUTIVE = FolderTemplate(
        name="executive",
        description="Board materials, strategic documents",
        folders=[
            "Board_Materials",
            "Board_Materials/2024",
            "Board_Materials/2025",
            "Strategy",
            "Confidential",
            "M&A",
            "Investor_Relations",
            "Legal",
        ],
        junk_files=[
            JunkFile("readme.txt", "EXECUTIVE DOCUMENTS\n===================\nSTRICTLY CONFIDENTIAL\nBoard Eyes Only"),
            JunkFile("Board_Materials/calendar.txt", "2025 Board Meetings:\n- Q1: March 15\n- Q2: June 12\n- Q3: September 18\n- Q4: December 4"),
            JunkFile("Confidential/handling.txt", "Document Handling:\n1. Do not print\n2. Do not forward\n3. Delete after meeting\n4. Report if found unattended"),
        ]
    )

    # =========================================================================
    # IT Department Scenario
    # =========================================================================
    IT_BACKUP = FolderTemplate(
        name="it_backup",
        description="IT infrastructure configs and backups",
        folders=[
            "Configs",
            "Configs/VPN",
            "Configs/Network",
            "Configs/Firewall",
            "Scripts",
            "Scripts/Automation",
            "Logs",
            "Backups",
            "Documentation",
            "Credentials",
        ],
        junk_files=[
            JunkFile("readme.txt", "IT Infrastructure Backup\n========================\nLast full backup: 2025-01-15\nRetention: 90 days"),
            JunkFile("Logs/backup.log", "2025-01-15 03:00:01 [INFO] Backup started\n2025-01-15 03:15:22 [INFO] Configs exported\n2025-01-15 03:30:45 [INFO] Scripts archived\n2025-01-15 03:45:22 [INFO] Backup completed successfully"),
            JunkFile("Scripts/readme.txt", "Automation Scripts\n------------------\nTest in dev before deploying to prod\nDocument all changes in changelog"),
            JunkFile("Documentation/inventory.txt", "Quick Reference:\n- DC01, DC02: Domain Controllers\n- FS01: File Server\n- SQL01: Database Server\n- VPN01: VPN Concentrator"),
        ]
    )

    # =========================================================================
    # Network Admin Scenario
    # =========================================================================
    NETWORK_ADMIN = FolderTemplate(
        name="network_admin",
        description="Network configurations and diagrams",
        folders=[
            "Network_Configs",
            "Network_Configs/Switches",
            "Network_Configs/Routers",
            "Wireless",
            "Firewall",
            "VPN",
            "Monitoring",
            "Diagrams",
            "Credentials",
        ],
        junk_files=[
            JunkFile("readme.txt", "NETWORK DOCUMENTATION\n=====================\nLast topology update: 2024-12\n\nFor emergencies: NOC ext 5555"),
            JunkFile("Monitoring/thresholds.txt", "Alert Thresholds:\n- CPU > 80%: Warning\n- CPU > 95%: Critical\n- Bandwidth > 70%: Warning\n- Packet loss > 1%: Critical"),
            JunkFile("Diagrams/changelog.txt", "Diagram Updates:\n2024-12: Added new branch office\n2024-10: Updated cloud connectivity\n2024-08: Refreshed core switches"),
        ]
    )

    # =========================================================================
    # Developer Scenario
    # =========================================================================
    DEVELOPER = FolderTemplate(
        name="developer",
        description="Development configs and code",
        folders=[
            "Projects",
            "Projects/Active",
            "Projects/Archive",
            "Configs",
            "Keys",
            "Documentation",
            "Scripts",
            "Backups",
        ],
        junk_files=[
            JunkFile("readme.txt", "DEV BACKUP\n==========\nContains sensitive config files\nDo not commit to version control"),
            JunkFile("Configs/.gitignore", "# Ignore sensitive files\n*.env\n*.pem\n*.key\ncredentials.json"),
            JunkFile("Projects/Active/notes.txt", "Current Sprint:\n- Feature: User authentication\n- Bug: Fix memory leak\n- Tech debt: Refactor API layer"),
            JunkFile("Keys/readme.txt", "API Keys\n--------\nRotate quarterly\nNever commit to git\nUse environment variables in prod"),
        ]
    )

    # =========================================================================
    # Project/Client Scenario
    # =========================================================================
    PROJECT = FolderTemplate(
        name="project",
        description="Project documentation and deliverables",
        folders=[
            "Project_Docs",
            "Archive",
            "Drafts",
            "Research",
            "Final",
            "Resources",
            "Meeting_Notes",
            "Client_Feedback",
        ],
        junk_files=[
            JunkFile("README.txt", "PROJECT ALPHA\n=============\nClient: Acme Corp\nPM: J. Williams\nStart: 2024-10-01\nTarget: 2025-03-31"),
            JunkFile("Archive/notes_v1.txt", "Initial project scope - superseded\nSee v2 in Project_Docs"),
            JunkFile("Meeting_Notes/standup.txt", "Daily Standup Format:\n1. What I did yesterday\n2. What I'm doing today\n3. Any blockers"),
            JunkFile("Drafts/wip.txt", "Work in Progress - Do Not Share\nLast updated: 2025-01"),
        ]
    )

    # =========================================================================
    # Security Audit Scenario
    # =========================================================================
    SECURITY_AUDIT = FolderTemplate(
        name="security_audit",
        description="Penetration test results and findings",
        folders=[
            "Audit_Reports",
            "Vulnerabilities",
            "Vulnerabilities/Critical",
            "Vulnerabilities/High",
            "Evidence",
            "Screenshots",
            "Credentials",
            "Tools",
            "Remediation",
        ],
        junk_files=[
            JunkFile("readme.txt", "SECURITY ASSESSMENT\n===================\nCLIENT CONFIDENTIAL\nAuthorized Personnel Only\n\nScope: Internal Network\nDate: 2024-12"),
            JunkFile("Vulnerabilities/summary.txt", "Finding Summary:\n- Critical: 2\n- High: 5\n- Medium: 12\n- Low: 23\n\nSee detailed reports for remediation steps"),
            JunkFile("Evidence/methodology.txt", "Testing Methodology:\n1. Reconnaissance\n2. Scanning\n3. Exploitation\n4. Post-exploitation\n5. Reporting"),
        ]
    )

    # =========================================================================
    # Training/Compliance Scenario
    # =========================================================================
    TRAINING = FolderTemplate(
        name="training",
        description="Training materials and compliance docs",
        folders=[
            "Required_Training",
            "Certifications",
            "Policy_Updates",
            "Resources",
            "Completed",
            "In_Progress",
        ],
        junk_files=[
            JunkFile("readme.txt", "MANDATORY TRAINING\n==================\nComplete all modules by end of quarter\n\nQuestions? Contact: training@company.com"),
            JunkFile("Required_Training/schedule.txt", "Training Deadlines:\n- Security Awareness: Q1\n- Anti-Harassment: Q2\n- Data Privacy: Q3\n- Code of Conduct: Q4"),
            JunkFile("Completed/log.txt", "Completion Log:\n- Security Awareness 2024: Completed 2024-03-15\n- Anti-Harassment 2024: Completed 2024-06-22"),
        ]
    )

    # =========================================================================
    # Contractor Scenario
    # =========================================================================
    CONTRACTOR = FolderTemplate(
        name="contractor",
        description="Contractor access and project docs",
        folders=[
            "Access_Info",
            "Project_Docs",
            "Credentials",
            "Timesheet",
            "Resources",
            "NDA",
        ],
        junk_files=[
            JunkFile("readme.txt", "CONTRACTOR ONBOARDING\n=====================\nWelcome! Please review all materials\n\nBadge pickup: Security Desk\nIT Support: helpdesk@company.com"),
            JunkFile("Access_Info/checklist.txt", "Setup Checklist:\n[ ] Sign NDA\n[ ] Get badge\n[ ] VPN setup\n[ ] Email configured\n[ ] Teams added"),
            JunkFile("Timesheet/instructions.txt", "Timesheet Submission:\n- Due: Every Friday by 5pm\n- Approver: Your PM\n- Portal: timesheets.company.com"),
        ]
    )

    # =========================================================================
    # Template Mapping
    # =========================================================================
    @classmethod
    def get_template(cls, scenario_type: str) -> FolderTemplate:
        """Get folder template for scenario type."""
        mapping = {
            # Personal scenarios
            "personal": cls.PERSONAL,
            "personal_backup": cls.PERSONAL,
            "social_creator": cls.SOCIAL_CREATOR,

            # Corporate scenarios
            "corporate": cls.CORPORATE,
            "hr": cls.HR_DOCUMENTS,
            "hr_documents": cls.HR_DOCUMENTS,
            "finance": cls.FINANCE,
            "executive": cls.EXECUTIVE,

            # Technical scenarios
            "it_department": cls.IT_BACKUP,
            "it_backup": cls.IT_BACKUP,
            "network_admin": cls.NETWORK_ADMIN,
            "developer": cls.DEVELOPER,
            "security_audit": cls.SECURITY_AUDIT,

            # Project scenarios
            "project": cls.PROJECT,
            "project_client": cls.PROJECT,
            "contractor": cls.CONTRACTOR,

            # Compliance
            "training": cls.TRAINING,
            "training_compliance": cls.TRAINING,
        }
        return mapping.get(scenario_type, cls.CORPORATE)

    @classmethod
    def list_templates(cls) -> List[Dict[str, str]]:
        """List all available templates."""
        templates = [
            cls.PERSONAL, cls.SOCIAL_CREATOR, cls.CORPORATE, cls.HR_DOCUMENTS,
            cls.FINANCE, cls.EXECUTIVE, cls.IT_BACKUP, cls.NETWORK_ADMIN,
            cls.DEVELOPER, cls.PROJECT, cls.SECURITY_AUDIT, cls.TRAINING,
            cls.CONTRACTOR
        ]
        return [
            {"name": t.name, "description": t.description, "folder_count": len(t.folders)}
            for t in templates
        ]


def get_system_files() -> List[JunkFile]:
    """Get system junk files (.DS_Store, Thumbs.db, etc.)."""
    return [
        JunkFile(".DS_Store", "", is_binary=True),
        JunkFile("Thumbs.db", "", is_binary=True),
        JunkFile(".Spotlight-V100", "", is_binary=True),
    ]


def get_junk_files_for_scenario(
    scenario_type: str,
    include_system_files: bool = True
) -> List[JunkFile]:
    """
    Get all junk files for a scenario.

    Args:
        scenario_type: The scenario type
        include_system_files: Whether to include .DS_Store, Thumbs.db, etc.

    Returns:
        List of junk files
    """
    template = FolderTemplates.get_template(scenario_type)
    files = list(template.junk_files)

    if include_system_files:
        files.extend(get_system_files())

    return files


def get_additional_folders(scenario_type: str) -> List[str]:
    """
    Get additional folders to create for a scenario.

    These are added to the profile's existing folder structure
    to make the drive look more realistic.
    """
    template = FolderTemplates.get_template(scenario_type)
    return template.folders


def generate_dynamic_content(template_name: str) -> str:
    """Generate dynamic content for a junk file with current date."""
    now = datetime.now()
    templates = {
        "backup_log": f"Backup Log\n==========\n{now.strftime('%Y-%m-%d %H:%M:%S')} Backup initiated\n{now.strftime('%Y-%m-%d %H:%M:%S')} Files copied: 247\n{now.strftime('%Y-%m-%d %H:%M:%S')} Backup complete",
        "last_sync": f"Last synchronized: {now.strftime('%B %d, %Y at %I:%M %p')}",
        "readme_date": f"Last updated: {now.strftime('%Y-%m')}",
    }
    return templates.get(template_name, "")
