"""URL path generator for believable tracking URLs."""

import random
import string
import hashlib
from typing import Optional
from enum import Enum


class UrlStyle(Enum):
    SHAREPOINT = "sharepoint"
    ONEDRIVE = "onedrive"
    GOOGLE_DRIVE = "google_drive"
    CORPORATE_PORTAL = "corporate_portal"
    DROPBOX = "dropbox"
    BOX = "box"
    GENERIC = "generic"


class UrlGenerator:
    """Generate believable URL paths for tracking links."""

    @classmethod
    def generate_path(
        cls,
        style: UrlStyle,
        token_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a believable URL path.

        Args:
            style: URL style to mimic
            token_id: Unique token identifier (will be encoded)
            filename: Optional filename to include

        Returns:
            URL path string
        """
        # Create a short, pronounceable ID from token
        short_id = cls._create_short_id(token_id)

        if style == UrlStyle.SHAREPOINT:
            return cls._sharepoint_path(short_id, filename)
        elif style == UrlStyle.ONEDRIVE:
            return cls._onedrive_path(short_id, filename)
        elif style == UrlStyle.GOOGLE_DRIVE:
            return cls._google_drive_path(short_id)
        elif style == UrlStyle.CORPORATE_PORTAL:
            return cls._corporate_portal_path(short_id, filename)
        elif style == UrlStyle.DROPBOX:
            return cls._dropbox_path(short_id)
        elif style == UrlStyle.BOX:
            return cls._box_path(short_id)
        else:
            return cls._generic_path(short_id)

    @classmethod
    def generate_full_url(
        cls,
        base_domain: str,
        style: UrlStyle,
        token_id: str,
        filename: Optional[str] = None,
        use_https: bool = True
    ) -> str:
        """
        Generate a full URL with domain.

        Args:
            base_domain: The base domain to use
            style: URL style to mimic
            token_id: Unique token identifier
            filename: Optional filename to include
            use_https: Whether to use HTTPS (default True)

        Returns:
            Full URL string
        """
        protocol = "https" if use_https else "http"
        path = cls.generate_path(style, token_id, filename)
        return f"{protocol}://{base_domain}{path}"

    @classmethod
    def get_style_for_scenario(cls, scenario_type: str) -> UrlStyle:
        """
        Get appropriate URL style for a scenario type.

        Args:
            scenario_type: The scenario type (e.g., 'corporate', 'personal')

        Returns:
            Appropriate UrlStyle
        """
        mapping = {
            "corporate": UrlStyle.SHAREPOINT,
            "hr": UrlStyle.SHAREPOINT,
            "finance": UrlStyle.SHAREPOINT,
            "executive": UrlStyle.SHAREPOINT,
            "it_department": UrlStyle.CORPORATE_PORTAL,
            "network_admin": UrlStyle.CORPORATE_PORTAL,
            "personal": UrlStyle.GOOGLE_DRIVE,
            "social_creator": UrlStyle.GOOGLE_DRIVE,
            "developer": UrlStyle.DROPBOX,
            "project": UrlStyle.DROPBOX,
        }
        return mapping.get(scenario_type, UrlStyle.GENERIC)

    @classmethod
    def _create_short_id(cls, token_id: str) -> str:
        """Create a short, pronounceable ID from token."""
        # Use hash to create deterministic but obscured ID
        hash_bytes = hashlib.sha256(token_id.encode()).digest()

        # Convert to base62 (alphanumeric)
        chars = string.ascii_letters + string.digits
        result = []
        num = int.from_bytes(hash_bytes[:8], 'big')

        while num and len(result) < 12:
            result.append(chars[num % 62])
            num //= 62

        return ''.join(result)

    @classmethod
    def _sharepoint_path(cls, short_id: str, filename: Optional[str]) -> str:
        """Generate SharePoint-style path."""
        safe_filename = cls._url_encode_filename(filename) if filename else "document"
        paths = [
            f"/_layouts/15/guestaccess.aspx?docid={short_id}",
            f"/sites/shared/Shared%20Documents/{safe_filename}",
            f"/:x:/g/personal/user/{short_id}/",
            f"/sites/team/_layouts/download.aspx?UniqueId={short_id}",
            f"/_layouts/15/Doc.aspx?sourcedoc={short_id}",
        ]
        return random.choice(paths)

    @classmethod
    def _onedrive_path(cls, short_id: str, filename: Optional[str]) -> str:
        """Generate OneDrive-style path."""
        paths = [
            f"/personal/_layouts/download.aspx?UniqueId={short_id}",
            f"/?id={short_id}&cid={short_id[:8]}",
            f"/download?resid={short_id}",
            f"/:w:/g/personal/{short_id}",
        ]
        return random.choice(paths)

    @classmethod
    def _google_drive_path(cls, short_id: str) -> str:
        """Generate Google Drive-style path."""
        paths = [
            f"/file/d/{short_id}/view?usp=sharing",
            f"/open?id={short_id}",
            f"/uc?id={short_id}&export=download",
            f"/file/d/{short_id}/view?usp=drive_link",
        ]
        return random.choice(paths)

    @classmethod
    def _dropbox_path(cls, short_id: str) -> str:
        """Generate Dropbox-style path."""
        paths = [
            f"/s/{short_id}",
            f"/scl/fi/{short_id}",
            f"/sh/{short_id[:8]}/{short_id[8:]}",
        ]
        return random.choice(paths)

    @classmethod
    def _box_path(cls, short_id: str) -> str:
        """Generate Box-style path."""
        paths = [
            f"/s/{short_id}",
            f"/shared/static/{short_id}",
            f"/file/{short_id}",
        ]
        return random.choice(paths)

    @classmethod
    def _corporate_portal_path(cls, short_id: str, filename: Optional[str]) -> str:
        """Generate corporate portal-style path."""
        departments = ["hr", "finance", "it", "legal", "ops", "admin"]
        doc_types = ["documents", "reports", "policies", "forms", "resources"]

        dept = random.choice(departments)
        doc_type = random.choice(doc_types)
        safe_filename = cls._url_encode_filename(filename) if filename else "document"

        paths = [
            f"/portal/{dept}/{doc_type}/{short_id}",
            f"/intranet/download/{short_id}",
            f"/resources/{doc_type}/view/{short_id}",
            f"/docs/{dept}/{safe_filename}",
            f"/internal/{doc_type}/{short_id}",
        ]
        return random.choice(paths)

    @classmethod
    def _generic_path(cls, short_id: str) -> str:
        """Generate generic short path."""
        paths = [
            f"/d/{short_id}",
            f"/f/{short_id}",
            f"/view/{short_id}",
            f"/dl/{short_id}",
        ]
        return random.choice(paths)

    @classmethod
    def _url_encode_filename(cls, filename: str) -> str:
        """URL encode a filename for path inclusion."""
        # Replace spaces with %20, keep alphanumeric and some safe chars
        safe_chars = set(string.ascii_letters + string.digits + "-_.")
        result = []
        for char in filename:
            if char in safe_chars:
                result.append(char)
            elif char == " ":
                result.append("%20")
            else:
                result.append(f"%{ord(char):02X}")
        return "".join(result)


def get_available_styles() -> list[str]:
    """Get list of available URL styles."""
    return [style.value for style in UrlStyle]
