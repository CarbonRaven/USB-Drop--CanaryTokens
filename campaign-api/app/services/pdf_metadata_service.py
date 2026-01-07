"""PDF metadata injection service."""

from pypdf import PdfReader, PdfWriter
from datetime import datetime, timedelta
from io import BytesIO
import random
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class PdfMetadataService:
    """Inject realistic metadata into PDF documents."""

    # Legitimate PDF Producer values (what generated the PDF)
    PRODUCERS = [
        "Adobe PDF Library 23.1.175",
        "Adobe PDF Library 21.7.85",
        "Adobe PDF Library 15.0",
        "Adobe PDF Library 16.0.0",
        "Microsoft: Print To PDF",
        "macOS Version 14.2 (Build 23C64) Quartz PDFContext",
        "macOS Version 13.5 (Build 22G74) Quartz PDFContext",
        "GPL Ghostscript 10.02.1",
        "Skia/PDF m120",
        "iText 7.2.5",
    ]

    # Legitimate Creator applications (what created the source document)
    CREATORS = [
        "Microsoft Word",
        "Microsoft Word for Microsoft 365",
        "Microsoft Excel",
        "Microsoft Excel for Microsoft 365",
        "Microsoft PowerPoint",
        "Microsoft PowerPoint for Microsoft 365",
        "Adobe Acrobat Pro DC (23.006.20360)",
        "Adobe Acrobat Pro 2020",
        "Adobe InDesign 2024 (Windows)",
        "Adobe InDesign 2023 (Windows)",
        "Google Docs",
        "Pages",
        "LibreOffice 7.6",
    ]

    # Author names
    AUTHORS = [
        "Jennifer Williams",
        "Michael Chen",
        "Sarah Johnson",
        "David Kim",
        "Emily Rodriguez",
        "James Wilson",
        "Amanda Thompson",
        "Robert Martinez",
        "Lisa Anderson",
        "Christopher Lee",
        "Jessica Brown",
        "Daniel Taylor",
    ]

    # Department-specific author pools
    DEPARTMENT_AUTHORS = {
        "hr": [
            "Sandra Mitchell",
            "Thomas Wright",
            "Karen Phillips",
            "Richard Moore",
        ],
        "finance": [
            "Patricia Clark",
            "Steven Hall",
            "Nancy Allen",
            "George Young",
        ],
        "it_department": [
            "Brian Scott",
            "Melissa Green",
            "Jeffrey Adams",
            "Laura Nelson",
        ],
        "executive": [
            "John Smith",
            "Elizabeth Carter",
            "William Turner",
            "Margaret Hill",
        ],
        "legal": [
            "Andrew Patterson",
            "Christine Hayes",
            "Marcus Webb",
            "Diana Foster",
        ],
    }

    # Producer/Creator combinations that make sense together
    PRODUCER_CREATOR_PAIRS = [
        ("Adobe PDF Library 23.1.175", "Microsoft Word for Microsoft 365"),
        ("Adobe PDF Library 23.1.175", "Microsoft Excel for Microsoft 365"),
        ("Adobe PDF Library 21.7.85", "Microsoft Word"),
        ("Microsoft: Print To PDF", "Microsoft Word for Microsoft 365"),
        ("Microsoft: Print To PDF", "Microsoft Excel for Microsoft 365"),
        ("Microsoft: Print To PDF", "Microsoft PowerPoint for Microsoft 365"),
        ("macOS Version 14.2 (Build 23C64) Quartz PDFContext", "Pages"),
        ("macOS Version 13.5 (Build 22G74) Quartz PDFContext", "Pages"),
        ("Adobe PDF Library 23.1.175", "Adobe Acrobat Pro DC (23.006.20360)"),
        ("Adobe PDF Library 21.7.85", "Adobe InDesign 2023 (Windows)"),
        ("iText 7.2.5", "Google Docs"),
    ]

    @classmethod
    def get_authors_for_scenario(cls, scenario_type: Optional[str] = None) -> List[str]:
        """Get appropriate author pool for scenario."""
        if scenario_type and scenario_type in cls.DEPARTMENT_AUTHORS:
            return cls.DEPARTMENT_AUTHORS[scenario_type] + cls.AUTHORS[:4]
        return cls.AUTHORS

    @classmethod
    def get_producer_creator_pair(cls) -> tuple:
        """Get a realistic producer/creator combination."""
        return random.choice(cls.PRODUCER_CREATOR_PAIRS)

    @classmethod
    def enhance_pdf(
        cls,
        pdf_data: bytes,
        author: Optional[str] = None,
        title: Optional[str] = None,
        subject: Optional[str] = None,
        producer: Optional[str] = None,
        creator: Optional[str] = None,
        created: Optional[datetime] = None,
        modified: Optional[datetime] = None,
        scenario_type: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> bytes:
        """
        Enhance PDF with realistic metadata.

        Args:
            pdf_data: Raw PDF bytes
            author: Document author (random if None)
            title: Document title
            subject: Document subject
            producer: PDF producer application (random if None)
            creator: Creator application (random if None)
            created: Creation date (random if None)
            modified: Modification date (random if None)
            scenario_type: Scenario for context-appropriate metadata
            keywords: Document keywords

        Returns:
            Enhanced PDF bytes
        """
        try:
            reader = PdfReader(BytesIO(pdf_data))
            writer = PdfWriter()

            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)

            # Get authors for scenario
            authors = cls.get_authors_for_scenario(scenario_type)

            # Set defaults
            if author is None:
                author = random.choice(authors)

            # Use a matching producer/creator pair for realism
            if producer is None and creator is None:
                producer, creator = cls.get_producer_creator_pair()
            elif producer is None:
                producer = random.choice(cls.PRODUCERS)
            elif creator is None:
                creator = random.choice(cls.CREATORS)

            if modified is None:
                modified = datetime.now() - timedelta(days=random.randint(1, 30))
            if created is None:
                created = modified - timedelta(days=random.randint(30, 180))

            # Format dates for PDF
            created_str = cls._format_pdf_date(created)
            modified_str = cls._format_pdf_date(modified)

            # Build metadata dictionary
            metadata = {
                '/Author': author,
                '/Producer': producer,
                '/Creator': creator,
                '/CreationDate': created_str,
                '/ModDate': modified_str,
            }

            if title:
                metadata['/Title'] = title
            if subject:
                metadata['/Subject'] = subject
            if keywords:
                metadata['/Keywords'] = keywords

            # Update metadata
            writer.add_metadata(metadata)

            # Write to bytes
            output = BytesIO()
            writer.write(output)

            logger.debug(f"Enhanced PDF: author={author}, producer={producer[:30]}...")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to enhance PDF metadata: {e}")
            return pdf_data  # Return original on failure

    @classmethod
    def _format_pdf_date(cls, dt: datetime) -> str:
        """
        Format datetime for PDF metadata.

        PDF date format: D:YYYYMMDDHHmmSS+HH'mm' or D:YYYYMMDDHHmmSSZ
        """
        # Use Z for UTC timezone (simpler and common)
        return dt.strftime("D:%Y%m%d%H%M%SZ")

    @classmethod
    def strip_metadata(cls, pdf_data: bytes) -> bytes:
        """
        Remove all metadata from a PDF.

        Useful for removing traces before adding custom metadata.
        """
        try:
            reader = PdfReader(BytesIO(pdf_data))
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Add empty metadata to overwrite
            writer.add_metadata({})

            output = BytesIO()
            writer.write(output)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to strip PDF metadata: {e}")
            return pdf_data

    @classmethod
    def get_metadata(cls, pdf_data: bytes) -> Dict[str, str]:
        """Extract current metadata from a PDF for inspection."""
        try:
            reader = PdfReader(BytesIO(pdf_data))
            metadata = reader.metadata
            if metadata:
                return {k: str(v) for k, v in metadata.items()}
            return {}
        except Exception as e:
            logger.error(f"Failed to read PDF metadata: {e}")
            return {}


def enhance_pdf(
    pdf_data: bytes,
    scenario_type: Optional[str] = None,
    file_timestamp: Optional[datetime] = None,
    **kwargs
) -> bytes:
    """
    Convenience function to enhance a PDF document.

    Args:
        pdf_data: Raw PDF bytes
        scenario_type: Scenario for context-appropriate metadata
        file_timestamp: Use this as the modified date
        **kwargs: Additional arguments passed to enhance method

    Returns:
        Enhanced PDF bytes
    """
    if file_timestamp:
        kwargs['modified'] = file_timestamp

    return PdfMetadataService.enhance_pdf(
        pdf_data,
        scenario_type=scenario_type,
        **kwargs
    )


def get_available_producers() -> List[str]:
    """Get list of available PDF producer values."""
    return PdfMetadataService.PRODUCERS


def get_available_creators() -> List[str]:
    """Get list of available PDF creator applications."""
    return PdfMetadataService.CREATORS
