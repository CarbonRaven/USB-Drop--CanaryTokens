"""Timestamp randomization service for realistic file metadata."""

from datetime import datetime, timedelta
import random
from enum import Enum
from typing import Dict, Tuple, Optional


class ScenarioType(Enum):
    """Scenario types for timestamp generation."""
    CORPORATE = "corporate"
    PERSONAL = "personal"
    IT_TECHNICAL = "it_technical"
    EXECUTIVE = "executive"


class TimestampService:
    """Generate realistic file timestamps based on scenario type."""

    # Timestamp ranges in days for each scenario type
    RANGES: Dict[ScenarioType, Dict[str, Tuple[int, int]]] = {
        ScenarioType.CORPORATE: {
            "created": (60, 180),      # 2-6 months ago
            "modified": (1, 30),       # 1-30 days ago
            "accessed": (0, 3),        # 0-3 days ago
        },
        ScenarioType.PERSONAL: {
            "created": (180, 730),     # 6 months - 2 years ago
            "modified": (30, 180),     # 1-6 months ago
            "accessed": (0, 7),        # 0-7 days ago
        },
        ScenarioType.IT_TECHNICAL: {
            "created": (30, 90),       # 1-3 months ago
            "modified": (1, 14),       # 1-14 days ago
            "accessed": (0, 1),        # 0-1 days ago
        },
        ScenarioType.EXECUTIVE: {
            "created": (14, 60),       # 2 weeks - 2 months ago
            "modified": (1, 7),        # 1-7 days ago
            "accessed": (0, 1),        # 0-1 days ago
        },
    }

    # Map profile scenario types to timestamp scenario types
    SCENARIO_MAP: Dict[str, ScenarioType] = {
        "hr": ScenarioType.CORPORATE,
        "hr_documents": ScenarioType.CORPORATE,
        "finance": ScenarioType.CORPORATE,
        "executive": ScenarioType.EXECUTIVE,
        "it_department": ScenarioType.IT_TECHNICAL,
        "network_admin": ScenarioType.IT_TECHNICAL,
        "developer": ScenarioType.IT_TECHNICAL,
        "personal": ScenarioType.PERSONAL,
        "social_creator": ScenarioType.PERSONAL,
        "training": ScenarioType.CORPORATE,
        "project": ScenarioType.CORPORATE,
        "contractor": ScenarioType.CORPORATE,
        "security_audit": ScenarioType.IT_TECHNICAL,
    }

    @classmethod
    def get_scenario_type(cls, profile_scenario: Optional[str]) -> ScenarioType:
        """
        Get the timestamp scenario type for a profile scenario.

        Args:
            profile_scenario: Profile scenario type string

        Returns:
            Corresponding ScenarioType enum value
        """
        if not profile_scenario:
            return ScenarioType.CORPORATE
        return cls.SCENARIO_MAP.get(profile_scenario, ScenarioType.CORPORATE)

    @classmethod
    def generate_timestamps(
        cls,
        scenario_type: ScenarioType = ScenarioType.CORPORATE,
        base_date: Optional[datetime] = None
    ) -> Dict[str, datetime]:
        """
        Generate realistic created, modified, and accessed timestamps.

        Args:
            scenario_type: Type of scenario for appropriate ranges
            base_date: Base date for calculations (default: now)

        Returns:
            dict with 'created', 'modified', 'accessed' datetime objects
        """
        if base_date is None:
            base_date = datetime.utcnow()

        ranges = cls.RANGES[scenario_type]

        # Generate random timestamps within ranges
        created = base_date - timedelta(
            days=random.randint(*ranges["created"]),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        modified = base_date - timedelta(
            days=random.randint(*ranges["modified"]),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        accessed = base_date - timedelta(
            days=random.randint(*ranges["accessed"]),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        # Ensure logical order: created <= modified <= accessed
        if modified < created:
            modified = created + timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 12)
            )
        if accessed < modified:
            accessed = modified + timedelta(
                hours=random.randint(1, 48),
                minutes=random.randint(0, 59)
            )

        return {
            "created": created,
            "modified": modified,
            "accessed": accessed,
        }

    @classmethod
    def generate_editing_time(cls, page_count: int = 1, doc_type: str = "document") -> int:
        """
        Generate realistic editing time in minutes based on document length.

        Args:
            page_count: Number of pages in document
            doc_type: Type of document (document, spreadsheet, presentation)

        Returns:
            Editing time in minutes
        """
        # Base time varies by document type
        if doc_type == "spreadsheet":
            base_per_page = random.randint(20, 40)
            overhead = random.randint(15, 45)
        elif doc_type == "presentation":
            base_per_page = random.randint(25, 45)
            overhead = random.randint(20, 60)
        else:  # document
            base_per_page = random.randint(15, 30)
            overhead = random.randint(10, 30)

        variance = random.uniform(0.8, 1.2)
        total = int((page_count * base_per_page + overhead) * variance)

        return max(15, total)  # Minimum 15 minutes

    @classmethod
    def format_for_zip(cls, dt: datetime) -> Tuple[int, int, int, int, int, int]:
        """
        Format datetime for ZIP file timestamp.

        Args:
            dt: datetime object

        Returns:
            Tuple of (year, month, day, hour, minute, second)
        """
        return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    @classmethod
    def format_for_exif(cls, dt: datetime) -> str:
        """
        Format datetime for EXIF metadata.

        Args:
            dt: datetime object

        Returns:
            EXIF-formatted date string (YYYY:MM:DD HH:MM:SS)
        """
        return dt.strftime("%Y:%m:%d %H:%M:%S")

    @classmethod
    def format_for_pdf(cls, dt: datetime, tz_offset: str = "+00'00'") -> str:
        """
        Format datetime for PDF metadata.

        Args:
            dt: datetime object
            tz_offset: Timezone offset string

        Returns:
            PDF-formatted date string
        """
        return f"D:{dt.strftime('%Y%m%d%H%M%S')}{tz_offset}"

    @classmethod
    def format_for_office(cls, dt: datetime) -> str:
        """
        Format datetime for Office document metadata (ISO format).

        Args:
            dt: datetime object

        Returns:
            ISO-formatted date string
        """
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def generate_file_timestamps_batch(
        cls,
        file_count: int,
        scenario_type: ScenarioType = ScenarioType.CORPORATE,
        base_date: Optional[datetime] = None
    ) -> list:
        """
        Generate timestamps for multiple files with realistic variation.

        Files created around the same time should have similar but not
        identical timestamps.

        Args:
            file_count: Number of files to generate timestamps for
            scenario_type: Type of scenario
            base_date: Base date for calculations

        Returns:
            List of timestamp dictionaries
        """
        if base_date is None:
            base_date = datetime.utcnow()

        # Generate a "batch creation" time range
        ranges = cls.RANGES[scenario_type]
        batch_start = base_date - timedelta(days=random.randint(*ranges["created"]))

        timestamps = []
        for i in range(file_count):
            # Each file created within a few days of batch start
            file_created = batch_start + timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )

            # Modified more recently
            file_modified = base_date - timedelta(
                days=random.randint(*ranges["modified"]),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # Ensure modified is after created
            if file_modified < file_created:
                file_modified = file_created + timedelta(
                    days=random.randint(1, 14),
                    hours=random.randint(0, 12)
                )

            # Accessed most recently
            file_accessed = base_date - timedelta(
                days=random.randint(*ranges["accessed"]),
                hours=random.randint(0, 12)
            )

            if file_accessed < file_modified:
                file_accessed = file_modified + timedelta(
                    hours=random.randint(1, 24)
                )

            timestamps.append({
                "created": file_created,
                "modified": file_modified,
                "accessed": file_accessed,
            })

        return timestamps
