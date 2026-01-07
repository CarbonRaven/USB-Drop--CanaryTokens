"""USB Drive builder service - creates tokens and prepares ZIP files."""

import os
import io
import zipfile
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import logging

from app.models.drive import Drive
from app.models.profile import Profile
from app.models.token import Token
from app.models.short_url import ShortUrl
from app.models.profile_file import ProfileFile
from app.services.canary_client import CanaryTokensClient
from app.services.shlink_client import ShlinkClient, ShlinkError
from app.services.content_templates import generate_text_content, TEXT_TEMPLATES, TEMPLATE_IMAGES
from app.services.timestamp_service import TimestampService, ScenarioType
from app.services.exif_service import inject_exif, get_available_cameras
from app.services.office_metadata_service import enhance_office_document
from app.services.pdf_metadata_service import enhance_pdf
from app.services.folder_templates import get_junk_files_for_scenario, JunkFile
from app.services.document_injector import document_injector
from app.services.shortcut_generator import shortcut_generator
from app.services.file_storage import file_storage
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Mapping of token types to download formats
TOKEN_FORMATS = {
    "ms_word": "msword",
    "ms_excel": "msexcel",
    "pdf": "pdf",
    "qr_code": "qr_code",
}


class USBBuilder:
    """Service for building USB drive content."""

    def __init__(self, db: Session):
        self.db = db
        self.canary_client = CanaryTokensClient()
        self.shlink_client = ShlinkClient()
        self.uploads_dir = "uploads"

    async def prepare_drive(self, drive: Drive, profile: Profile) -> dict:
        """
        Prepare a drive by creating all tokens defined in the profile.

        Returns:
            Files manifest dictionary
        """
        token_config = profile.token_config or {}
        file_structure = profile.file_structure or {}

        # URL styling configuration (for believable links)
        styled_domain = token_config.get("styled_domain")  # e.g., "docs.internal-corp.com"
        url_style = token_config.get("url_style")  # e.g., "sharepoint", "onedrive"
        scenario_type = profile.scenario_type  # Used to auto-select URL style if not specified

        # Get campaign landing page URL (overrides per-file redirect themes)
        campaign = drive.campaign
        campaign_landing_url = self._get_campaign_landing_url(campaign)
        if campaign_landing_url:
            logger.info(f"Using campaign landing page: {campaign_landing_url}")

        files = []
        total_size = 0

        # Create folders
        folders = file_structure.get("folders", [])

        # Process file definitions
        for file_def in file_structure.get("files", []):
            filename = file_def.get("name", "")
            folder = file_def.get("folder", "")
            token_type = file_def.get("type", "")
            redirect_theme = file_def.get("redirect_theme", "")
            text_template = file_def.get("template", "")
            custom_content = file_def.get("custom_content", "")

            if not filename or not token_type:
                continue

            # Map old token type names to new ones
            token_type = self._normalize_token_type(token_type)

            # Handle template images (pre-generated, no token needed)
            if token_type == "template_image":
                source_file = file_def.get("source", "")
                file_path = f"{folder}/{filename}" if folder else filename
                files.append({
                    "path": file_path,
                    "token_type": token_type,
                    "source": source_file,
                    "template_id": profile.scenario_type,
                    "size_bytes": 0,  # Size calculated when adding to ZIP
                    "created_at": datetime.utcnow().isoformat(),
                })
                continue

            # Build file path
            file_path = f"{folder}/{filename}" if folder else filename

            # Check if file has custom content with placeholders
            if custom_content:
                # For custom content, ensure the file has a .txt extension
                # since we're outputting plain text content
                custom_filename = filename
                custom_file_path = file_path
                if token_type in ["ms_word", "ms_excel", "pdf"]:
                    # Change extension to .txt for document types with custom content
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    custom_filename = f"{base_name}.txt"
                    custom_file_path = f"{folder}/{custom_filename}" if folder else custom_filename
                    logger.info(f"Custom content file {filename} -> {custom_filename} (text output)")

                # Process as custom template with placeholder replacement
                file_info = await self._process_custom_content_file(
                    drive, custom_file_path, custom_filename, token_type, custom_content,
                    campaign_landing_url, styled_domain, url_style
                )
                if file_info:
                    files.append(file_info)
                    total_size += file_info.get("size_bytes", 0)
                continue

            # Create memo for this token
            memo = f"{drive.unique_code}|{file_path}"

            # Determine redirect URL (campaign config overrides per-file theme)
            redirect_url = None
            if campaign_landing_url:
                redirect_url = campaign_landing_url
            elif redirect_theme:
                redirect_url = self._get_redirect_url(redirect_theme)

            # For text files, we create a web token to embed in the content
            actual_token_type = token_type
            if token_type == "text":
                actual_token_type = "web"

            # Create the token
            try:
                result = await self._create_token(
                    token_type=actual_token_type,
                    memo=memo,
                    redirect_url=redirect_url,
                )

                if not result:
                    logger.error(f"Failed to create token for {file_path}")
                    continue

                # Extract token data
                canary_data = result.get("canarytoken", {})
                canary_token_id = canary_data.get("canarytoken", "")
                auth_token = canary_data.get("auth_token", "")
                token_url = canary_data.get("url", "") or canary_data.get("hostname", "")

                # For text files, build the full tracking URL
                if token_type == "text":
                    token_url = result.get("token_url", "") or f"http://{token_url}"

                # Create token record
                token = Token(
                    drive_id=drive.id,
                    canary_token_id=canary_token_id,
                    auth_token=auth_token,
                    token_type=token_type,
                    filename=filename,
                    file_path=file_path,
                    memo=memo,
                    url=token_url,
                    redirect_url=redirect_url,
                    redirect_theme=redirect_theme,
                    aws_access_key_id=result.get("access_key_id"),
                    aws_secret_access_key=result.get("secret_access_key"),
                )
                self.db.add(token)

                # Calculate file size
                file_size = 0
                if token_type in ["ms_word", "ms_excel", "pdf", "qr_code"]:
                    try:
                        fmt = TOKEN_FORMATS.get(token_type, "msword")
                        content = await self.canary_client.download_token(
                            canary_token_id, auth_token, fmt
                        )
                        file_size = len(content) if content else 0
                    except Exception as e:
                        logger.error(f"Failed to check token file size: {e}")
                elif token_type == "text":
                    # Generate text content to get size (with optional styled URLs)
                    # Use a default template if none specified
                    template_to_use = text_template if text_template else "password_list"
                    text_content = generate_text_content(
                        template_to_use,
                        token_url,
                        styled_domain=styled_domain,
                        url_style=url_style,
                        scenario_type=scenario_type,
                    )
                    file_size = len(text_content.encode()) if text_content else 0

                total_size += file_size

                files.append({
                    "path": file_path,
                    "token_id": canary_token_id,
                    "auth_token": auth_token,
                    "token_type": token_type,
                    "text_template": text_template,
                    "token_url": token_url,
                    "size_bytes": file_size,
                    "created_at": datetime.utcnow().isoformat(),
                })

            except Exception as e:
                logger.error(f"Error creating token for {file_path}: {e}")
                continue

        self.db.commit()

        # Process uploaded files (ProfileFile records)
        uploaded_files = await self._process_uploaded_files(
            drive, profile, campaign_landing_url, styled_domain, url_style
        )
        files.extend(uploaded_files)

        # Create short URLs if url_config is enabled
        # Drive url_config overrides profile url_config (but empty dict {} doesn't count)
        url_config = drive.url_config if drive.url_config else (profile.url_config or {})
        if url_config.get("enabled"):
            await self._create_short_urls_for_drive(drive, url_config, files)

        return {
            "folders": folders,
            "files": files,
            "total_size_bytes": total_size,
            "file_count": len(files),
            "prepared_at": datetime.utcnow().isoformat(),
        }

    def _normalize_token_type(self, token_type: str) -> str:
        """Normalize old token type names to new format."""
        mappings = {
            "doc-msword": "ms_word",
            "doc-msexcel": "ms_excel",
            "pdf-acrobat-reader": "pdf",
            "windows-dir": "windows_dir",
            "qr-code": "qr_code",
            "aws-id": "aws_keys",
        }
        return mappings.get(token_type, token_type)

    async def _create_token(
        self,
        token_type: str,
        memo: str,
        redirect_url: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a token using the appropriate method."""
        try:
            if token_type == "dns":
                return await self.canary_client.create_dns_token(memo)
            elif token_type == "ms_word":
                return await self.canary_client.create_word_token(memo)
            elif token_type == "ms_excel":
                return await self.canary_client.create_excel_token(memo)
            elif token_type == "pdf":
                return await self.canary_client.create_pdf_token(memo)
            elif token_type == "windows_dir":
                return await self.canary_client.create_folder_token(memo)
            elif token_type == "aws_keys":
                return await self.canary_client.create_aws_token(memo)
            elif token_type == "qr_code":
                return await self.canary_client.create_qr_token(memo, redirect_url or "https://example.com")
            elif token_type in ["web", "http"]:
                return await self.canary_client.create_web_token(memo, redirect_url)
            else:
                logger.warning(f"Unknown token type: {token_type}")
                return await self.canary_client.create_token(token_type=token_type, memo=memo)
        except Exception as e:
            logger.error(f"Failed to create {token_type} token: {e}")
            return None

    def _get_redirect_url(self, theme: str) -> str:
        """Get redirect URL based on theme."""
        base_url = f"https://rick.{settings.canary_domain}"

        # All available themes from the rickroll landing page server
        theme_urls = {
            "rickroll": f"{base_url}/direct",
            "direct": f"{base_url}/direct",
            "corporate": f"{base_url}/corporate",
            "login": f"{base_url}/login",
            "maintenance": f"{base_url}/maintenance",
            "helpdesk": f"{base_url}/helpdesk",
            "hrportal": f"{base_url}/hrportal",
            "fileshare": f"{base_url}/fileshare",
            "training": f"{base_url}/training",
            "banking": f"{base_url}/banking",
            "document": f"{base_url}/document",
            "survey": f"{base_url}/survey",
            "onlyfans": f"{base_url}/onlyfans",
        }

        return theme_urls.get(theme, f"{base_url}/direct")

    def _get_campaign_landing_url(self, campaign) -> Optional[str]:
        """Get landing page URL from campaign config, including delay parameter."""
        if not campaign or not campaign.landing_page_config:
            return None

        config = campaign.landing_page_config
        mode = config.get("mode", "disabled")
        delay_seconds = config.get("delay_seconds", 3)  # Default 3 seconds

        base_url = None
        if mode == "disabled":
            return None
        elif mode == "included":
            theme = config.get("included_theme", "corporate")
            base_url = self._get_redirect_url(theme)
        elif mode == "custom_url":
            base_url = config.get("custom_url")

        # Append delay parameter if we have a URL
        if base_url:
            separator = "&" if "?" in base_url else "?"
            return f"{base_url}{separator}delay={delay_seconds}"

        return None

    async def _process_uploaded_files(
        self,
        drive: Drive,
        profile: Profile,
        campaign_landing_url: Optional[str],
        styled_domain: Optional[str],
        url_style: Optional[str],
    ) -> List[dict]:
        """
        Process uploaded ProfileFile records for inclusion in the drive.

        For documents (Word, Excel, PDF): Creates tokens and injects them
        For static files (images): Includes as-is
        For shortcuts: Generates .url/.webloc files
        For templates: Generates text files with placeholders replaced

        Returns:
            List of file info dicts for the manifest
        """
        files = []

        # Query uploaded files for this profile
        profile_files = self.db.query(ProfileFile).filter(
            ProfileFile.profile_id == profile.id
        ).order_by(ProfileFile.sort_order).all()

        for pf in profile_files:
            file_path = f"{pf.folder}/{pf.filename}" if pf.folder else pf.filename

            try:
                if pf.file_type == "document" and pf.token_type:
                    # Document with token to inject
                    file_info = await self._process_document_file(
                        drive, pf, file_path, campaign_landing_url
                    )
                    if file_info:
                        files.append(file_info)

                elif pf.file_type == "static":
                    # Static file (image) - include as-is
                    files.append({
                        "path": file_path,
                        "file_type": "static",
                        "profile_file_id": str(pf.id),
                        "stored_filename": pf.stored_filename,
                        "size_bytes": pf.file_size_bytes or 0,
                        "created_at": datetime.utcnow().isoformat(),
                    })

                elif pf.file_type == "shortcut":
                    # URL shortcut file - generate filenames now, regenerate content in create_zip
                    shortcut_files = shortcut_generator.generate_for_type(
                        pf.target_url,
                        pf.filename,
                        pf.shortcut_type or "both"
                    )
                    for sc_filename, sc_content in shortcut_files:
                        sc_path = f"{pf.folder}/{sc_filename}" if pf.folder else sc_filename
                        files.append({
                            "path": sc_path,
                            "file_type": "shortcut",
                            "profile_file_id": str(pf.id),
                            "target_url": pf.target_url,
                            "shortcut_type": pf.shortcut_type or "both",
                            # Don't store content (bytes) - regenerate in create_zip
                            "size_bytes": len(sc_content),
                            "created_at": datetime.utcnow().isoformat(),
                        })

                elif pf.file_type == "template":
                    # Custom template - create a web token for tracking
                    if pf.custom_content:
                        file_info = await self._process_template_file(
                            drive, pf, file_path, campaign_landing_url,
                            styled_domain, url_style
                        )
                        if file_info:
                            files.append(file_info)

            except Exception as e:
                logger.error(f"Error processing uploaded file {pf.filename}: {e}")
                continue

        return files

    async def _process_document_file(
        self,
        drive: Drive,
        profile_file: ProfileFile,
        file_path: str,
        campaign_landing_url: Optional[str],
    ) -> Optional[dict]:
        """Process an uploaded document file by creating a token and preparing for injection."""
        memo = f"{drive.unique_code}|{file_path}|uploaded"

        # Determine redirect URL
        redirect_url = campaign_landing_url

        # Create a web token for this document
        try:
            result = await self.canary_client.create_web_token(memo, redirect_url)

            if not result:
                logger.error(f"Failed to create token for uploaded file {file_path}")
                return None

            canary_data = result.get("canarytoken", {})
            canary_token_id = canary_data.get("canarytoken", "")
            auth_token = canary_data.get("auth_token", "")
            token_url = result.get("token_url", "") or canary_data.get("url", "")

            # Create token record
            token = Token(
                drive_id=drive.id,
                canary_token_id=canary_token_id,
                auth_token=auth_token,
                token_type=profile_file.token_type,
                filename=profile_file.filename,
                file_path=file_path,
                memo=memo,
                url=token_url,
                redirect_url=redirect_url,
            )
            self.db.add(token)
            self.db.commit()

            return {
                "path": file_path,
                "file_type": "document",
                "token_id": canary_token_id,
                "auth_token": auth_token,
                "token_type": profile_file.token_type,
                "token_url": token_url,
                "profile_file_id": str(profile_file.id),
                "stored_filename": profile_file.stored_filename,
                "mime_type": profile_file.mime_type,
                "size_bytes": profile_file.file_size_bytes or 0,
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating token for document {file_path}: {e}")
            return None

    def _find_token_placeholders(self, content: str) -> List[str]:
        """Find all {canary_token-TYPE} placeholders in content."""
        import re
        # Match {canary_token-URL}, {canary_token-DNS}, etc.
        pattern = r'\{canary_token-([A-Z]+)\}'
        matches = re.findall(pattern, content)
        # Return unique types
        return list(set(matches))

    def _map_placeholder_to_token_type(self, placeholder_type: str) -> str:
        """Map placeholder type (URL, DNS, WORD, etc.) to canary token type."""
        mapping = {
            "URL": "web",
            "DNS": "dns",
            "WORD": "ms_word",
            "EXCEL": "ms_excel",
            "PDF": "pdf",
            "QR": "qr_code",
        }
        return mapping.get(placeholder_type, "web")

    async def _process_template_file(
        self,
        drive: Drive,
        profile_file: ProfileFile,
        file_path: str,
        campaign_landing_url: Optional[str],
        styled_domain: Optional[str],
        url_style: Optional[str],
    ) -> Optional[dict]:
        """Process a custom template file by creating tokens for placeholders."""
        content = profile_file.custom_content or ""

        # Find all token placeholders (new format: {canary_token-URL}, {canary_token-DNS}, etc.)
        token_types = self._find_token_placeholders(content)

        # Also check for legacy {canary_url} placeholder
        has_legacy_placeholder = "{canary_url}" in content

        if not token_types and not has_legacy_placeholder:
            # No placeholders, just include as static text
            # Store as string, encode to bytes when creating ZIP
            return {
                "path": file_path,
                "file_type": "template",
                "profile_file_id": str(profile_file.id),
                "custom_content": content,  # Store as string for JSON serialization
                "token_urls": {},  # Empty dict, no tokens
                "size_bytes": len(content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat(),
            }

        # Create tokens for each placeholder type
        token_urls = {}  # Maps placeholder type to URL

        try:
            redirect_url = campaign_landing_url

            # Create tokens for new format placeholders
            for placeholder_type in token_types:
                memo = f"{drive.unique_code}|{file_path}|{placeholder_type}"
                actual_token_type = self._map_placeholder_to_token_type(placeholder_type)

                result = await self._create_token(
                    token_type=actual_token_type,
                    memo=memo,
                    redirect_url=redirect_url,
                )

                if result:
                    canary_data = result.get("canarytoken", {})
                    canary_token_id = canary_data.get("canarytoken", "")
                    auth_token = canary_data.get("auth_token", "")
                    token_url = result.get("token_url", "") or canary_data.get("url", "") or canary_data.get("hostname", "")

                    # Create token record
                    token = Token(
                        drive_id=drive.id,
                        canary_token_id=canary_token_id,
                        auth_token=auth_token,
                        token_type=actual_token_type,
                        filename=profile_file.filename,
                        file_path=file_path,
                        memo=memo,
                        url=token_url,
                        redirect_url=redirect_url,
                    )
                    self.db.add(token)

                    token_urls[placeholder_type] = token_url
                    logger.info(f"Created {placeholder_type} token for template {file_path}: {token_url}")

            # Create web token for legacy placeholder if present
            if has_legacy_placeholder:
                memo = f"{drive.unique_code}|{file_path}|legacy"
                result = await self.canary_client.create_web_token(memo, redirect_url)

                if result:
                    canary_data = result.get("canarytoken", {})
                    canary_token_id = canary_data.get("canarytoken", "")
                    auth_token = canary_data.get("auth_token", "")
                    token_url = result.get("token_url", "") or canary_data.get("url", "")

                    token = Token(
                        drive_id=drive.id,
                        canary_token_id=canary_token_id,
                        auth_token=auth_token,
                        token_type="web",
                        filename=profile_file.filename,
                        file_path=file_path,
                        memo=memo,
                        url=token_url,
                        redirect_url=redirect_url,
                    )
                    self.db.add(token)
                    token_urls["_legacy"] = token_url

            self.db.commit()

            return {
                "path": file_path,
                "file_type": "template",
                "token_type": "text",
                "token_urls": token_urls,  # Dict of placeholder type -> URL
                "profile_file_id": str(profile_file.id),
                "custom_content": content,
                "size_bytes": len(content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating tokens for template {file_path}: {e}")
            return None

    async def _process_custom_content_file(
        self,
        drive: Drive,
        file_path: str,
        filename: str,
        token_type: str,
        custom_content: str,
        campaign_landing_url: Optional[str],
        styled_domain: Optional[str],
        url_style: Optional[str],
    ) -> Optional[dict]:
        """
        Process a file definition that has custom_content with placeholders.

        This handles files created in the profile wizard where the user has
        added custom text content with {canary_token-TYPE} placeholders.

        Args:
            drive: The drive being prepared
            file_path: Full path for the file in the ZIP
            filename: Just the filename
            token_type: The declared token type (text, ms_word, pdf, etc.)
            custom_content: The user's custom content with placeholders
            campaign_landing_url: Optional redirect URL from campaign config
            styled_domain: Optional domain for URL styling
            url_style: Optional URL style preference

        Returns:
            File info dict for the manifest, or None on error
        """
        # Find all token placeholders in the content
        placeholder_types = self._find_token_placeholders(custom_content)

        # Also check for legacy {canary_url} placeholder
        has_legacy_placeholder = "{canary_url}" in custom_content

        if not placeholder_types and not has_legacy_placeholder:
            # No placeholders - just return as static content
            encoded_content = custom_content.encode('utf-8')
            return {
                "path": file_path,
                "file_type": "custom_content",
                "token_type": token_type,
                "custom_content": custom_content,
                "token_urls": {},
                "size_bytes": len(encoded_content),
                "created_at": datetime.utcnow().isoformat(),
            }

        # Create tokens for each placeholder type
        token_urls = {}
        redirect_url = campaign_landing_url

        try:
            for placeholder_type in placeholder_types:
                memo = f"{drive.unique_code}|{file_path}|{placeholder_type}"
                actual_token_type = self._map_placeholder_to_token_type(placeholder_type)

                result = await self._create_token(
                    token_type=actual_token_type,
                    memo=memo,
                    redirect_url=redirect_url,
                )

                if result:
                    canary_data = result.get("canarytoken", {})
                    canary_token_id = canary_data.get("canarytoken", "")
                    auth_token = canary_data.get("auth_token", "")
                    token_url = result.get("token_url", "") or canary_data.get("url", "") or canary_data.get("hostname", "")

                    # Create token record
                    token = Token(
                        drive_id=drive.id,
                        canary_token_id=canary_token_id,
                        auth_token=auth_token,
                        token_type=actual_token_type,
                        filename=filename,
                        file_path=file_path,
                        memo=memo,
                        url=token_url,
                        redirect_url=redirect_url,
                    )
                    self.db.add(token)
                    token_urls[placeholder_type] = token_url
                    logger.info(f"Created {placeholder_type} token for custom content file {file_path}: {token_url}")

            # Handle legacy {canary_url} placeholder
            if has_legacy_placeholder:
                memo = f"{drive.unique_code}|{file_path}|legacy"
                result = await self.canary_client.create_web_token(memo, redirect_url)

                if result:
                    canary_data = result.get("canarytoken", {})
                    canary_token_id = canary_data.get("canarytoken", "")
                    auth_token = canary_data.get("auth_token", "")
                    token_url = result.get("token_url", "") or canary_data.get("url", "")

                    token = Token(
                        drive_id=drive.id,
                        canary_token_id=canary_token_id,
                        auth_token=auth_token,
                        token_type="web",
                        filename=filename,
                        file_path=file_path,
                        memo=memo,
                        url=token_url,
                        redirect_url=redirect_url,
                    )
                    self.db.add(token)
                    token_urls["_legacy"] = token_url

            self.db.commit()

            return {
                "path": file_path,
                "file_type": "custom_content",
                "token_type": token_type,
                "custom_content": custom_content,
                "token_urls": token_urls,
                "size_bytes": len(custom_content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating tokens for custom content file {file_path}: {e}")
            return None

    def _count_url_placeholders(self, template_name: str) -> int:
        """Count how many {canary_url} placeholders are in a text template."""
        template = TEXT_TEMPLATES.get(template_name)
        if not template:
            return 1  # Default to 1 if template not found
        content = template.get("content", "")
        return content.count("{canary_url}")

    async def _create_short_urls_for_drive(self, drive: Drive, url_config: dict, files: List[dict]) -> None:
        """Create short URLs for all tokens on a drive.

        For text tokens, creates multiple short URLs (one per URL placeholder in template).

        Args:
            drive: The drive to create short URLs for
            url_config: URL shortener configuration
            files: List of file info dicts from prepare_drive (used to look up templates)
        """
        base_slug = url_config.get("base_slug", "")
        suffix_mode = url_config.get("suffix_mode", "random")
        suffix_length = url_config.get("suffix_length", 4)
        domain = url_config.get("domain")

        # Refresh drive to get tokens
        self.db.refresh(drive)

        # Build a lookup from token_id to file info (for template name)
        token_to_file = {}
        for file_info in files:
            token_id = file_info.get("token_id")
            if token_id:
                token_to_file[token_id] = file_info

        for token in drive.tokens or []:
            # Only create short URLs for tokens with URLs (web, text tokens)
            if not token.url:
                continue

            # Determine how many short URLs to create
            url_count = 1
            file_info = token_to_file.get(token.canary_token_id, {})
            if token.token_type == "text":
                template_name = file_info.get("text_template", "")
                if template_name:
                    url_count = max(1, self._count_url_placeholders(template_name))
                    logger.info(f"Token {token.id} uses template '{template_name}' with {url_count} URL placeholders")

            # Create short URLs for each position
            for position in range(url_count):
                try:
                    result = await self.shlink_client.create_drive_short_url(
                        canary_url=token.url,
                        base_slug=base_slug,
                        suffix_mode=suffix_mode,
                        drive_code=drive.unique_code,
                        drive_id=str(drive.id),
                        token_id=str(token.id),
                        suffix_length=suffix_length,
                        domain=domain,
                    )

                    short_url = ShortUrl(
                        drive_id=drive.id,
                        token_id=token.id,
                        position=position,
                        base_slug=result["base_slug"],
                        suffix_mode=result["suffix_mode"],
                        generated_suffix=result["generated_suffix"],
                        full_slug=result["full_slug"],
                        shlink_short_code=result["shortCode"],
                        shlink_domain=result.get("domain") or settings.shlink_default_domain,
                        canary_url=token.url,
                        short_url=result["shortUrl"],
                    )
                    self.db.add(short_url)
                    logger.info(f"Created short URL {position+1}/{url_count} for token {token.id}: {result['shortUrl']}")

                except ShlinkError as e:
                    logger.error(f"Failed to create short URL for token {token.id} position {position}: {e}")
                except Exception as e:
                    import traceback
                    logger.error(f"Unexpected error creating short URL for token {token.id} position {position}: {type(e).__name__}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

        self.db.commit()

    async def create_zip(self, drive: Drive) -> bytes:
        """Create a ZIP file containing all drive files with realistic timestamps."""
        zip_buffer = io.BytesIO()

        # Get scenario type for timestamp generation
        profile_scenario = None
        styled_domain = None
        url_style = None
        if drive.profile:
            profile_scenario = drive.profile.scenario_type
            token_config = drive.profile.token_config or {}
            styled_domain = token_config.get("styled_domain")
            url_style = token_config.get("url_style")
        scenario_type = TimestampService.get_scenario_type(profile_scenario)

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest = drive.files_manifest or {}
            files = manifest.get("files", [])

            # Generate timestamps for all files at once for realistic variation
            file_timestamps = TimestampService.generate_file_timestamps_batch(
                len(files) + len(manifest.get("folders", [])) + 1,  # +1 for README
                scenario_type
            )
            timestamp_index = 0

            # Create folders with realistic timestamps
            for folder in manifest.get("folders", []):
                ts = file_timestamps[timestamp_index]["modified"]
                zinfo = zipfile.ZipInfo(
                    filename=f"{folder}/",
                    date_time=TimestampService.format_for_zip(ts)
                )
                zf.writestr(zinfo, "")
                timestamp_index += 1

            # Add files with realistic timestamps
            for file_info in files:
                file_path = file_info.get("path", "")
                token_id = file_info.get("token_id", "")
                auth_token = file_info.get("auth_token", "")
                token_type = file_info.get("token_type", "")
                text_template = file_info.get("text_template", "")
                token_url = file_info.get("token_url", "")

                if not file_path:
                    continue

                # Get file_type for uploaded/special files
                file_type = file_info.get("file_type", "")

                # Skip files without token_id, except:
                # - template_image (pre-generated images)
                # - files with file_type (uploaded files, shortcuts, templates, custom_content)
                if not token_id and token_type != "template_image" and not file_type:
                    continue

                # Get timestamp for this file
                if timestamp_index < len(file_timestamps):
                    ts = file_timestamps[timestamp_index]["modified"]
                    timestamp_index += 1
                else:
                    ts = TimestampService.generate_timestamps(scenario_type)["modified"]

                try:
                    content = None

                    # Get file content based on token type
                    if token_type in ["ms_word", "ms_excel", "pdf", "qr_code"]:
                        fmt = TOKEN_FORMATS.get(token_type, "msword")
                        content = await self.canary_client.download_token(
                            token_id, auth_token, fmt
                        )

                        # Enhance Office documents with realistic metadata
                        if content and token_type in ["ms_word", "ms_excel"]:
                            content = enhance_office_document(
                                content,
                                doc_type=token_type,
                                scenario_type=profile_scenario,
                                file_timestamp=ts,
                            )
                            logger.debug(f"Enhanced {token_type} metadata for {file_path}")

                        # Enhance PDF documents with realistic metadata
                        elif content and token_type == "pdf":
                            content = enhance_pdf(
                                content,
                                scenario_type=profile_scenario,
                                file_timestamp=ts,
                            )
                            logger.debug(f"Enhanced PDF metadata for {file_path}")

                    elif token_type == "text":
                        # Collect all short URLs for this token (or use original URL)
                        urls_to_use = [token_url]  # Default to original
                        if token_id:
                            # Look up the token to get its short URLs
                            token_obj = self.db.query(Token).filter(
                                Token.canary_token_id == token_id
                            ).first()
                            if token_obj and token_obj.short_urls:
                                # Use short URLs ordered by position
                                urls_to_use = [su.short_url for su in token_obj.short_urls]
                                logger.info(f"Using {len(urls_to_use)} short URLs for {file_path}")

                        # Generate text content with embedded URLs (multiple short or single original)
                        # Use default template if none specified
                        template_to_use = text_template if text_template else "password_list"
                        text_content = generate_text_content(
                            template_to_use,
                            urls_to_use,  # Now passing a list
                            styled_domain=styled_domain,
                            url_style=url_style,
                            scenario_type=profile_scenario,
                        )
                        if text_content:
                            content = text_content.encode('utf-8')

                    elif token_type == "windows_dir":
                        # Create desktop.ini for folder token
                        token = self.db.query(Token).filter(
                            Token.canary_token_id == token_id
                        ).first()
                        if token and token.url:
                            ini_content = self._create_desktop_ini(token.url)
                            content = ini_content.encode('utf-8') if isinstance(ini_content, str) else ini_content

                    elif token_type == "aws_keys":
                        # Create AWS credentials file
                        token = self.db.query(Token).filter(
                            Token.canary_token_id == token_id
                        ).first()
                        if token:
                            creds_content = self._create_aws_credentials(
                                token.aws_access_key_id,
                                token.aws_secret_access_key,
                            )
                            content = creds_content.encode('utf-8') if isinstance(creds_content, str) else creds_content

                    elif token_type == "template_image":
                        # Copy pre-generated template image with EXIF injection
                        source_file = file_info.get("source", "")
                        template_id = file_info.get("template_id", "")
                        if source_file and template_id:
                            image_path = f"/app/uploads/template_images/{template_id}/{source_file}"
                            try:
                                with open(image_path, "rb") as img_file:
                                    raw_content = img_file.read()

                                # Inject realistic EXIF metadata
                                content = inject_exif(
                                    raw_content,
                                    camera=None,  # Random camera
                                    location=None,  # Random location
                                    photo_date=ts,  # Use the file's timestamp
                                    add_gps_variance=True,
                                    strip_existing=True,  # Remove any AI signatures
                                )
                                logger.debug(f"Injected EXIF into {file_path}")

                            except FileNotFoundError:
                                logger.warning(f"Template image not found: {image_path}")

                    # Handle uploaded files (ProfileFile types)
                    # file_type already retrieved at start of loop

                    if file_type == "document":
                        # Uploaded document - read from storage and inject token
                        stored_filename = file_info.get("stored_filename", "")
                        profile_file_id = file_info.get("profile_file_id", "")
                        token_url = file_info.get("token_url", "")
                        mime_type = file_info.get("mime_type", "")

                        if stored_filename and profile_file_id:
                            try:
                                # Read the stored file
                                profile_file = self.db.query(ProfileFile).filter(
                                    ProfileFile.id == profile_file_id
                                ).first()
                                if profile_file:
                                    raw_content = await file_storage.read_file(
                                        profile_file.profile_id, stored_filename
                                    )

                                    # Inject token into document
                                    if token_url and mime_type:
                                        content = document_injector.inject_from_bytes(
                                            raw_content,
                                            token_url,
                                            mime_type,
                                            profile_file.filename
                                        )
                                        logger.debug(f"Injected token into uploaded document {file_path}")
                                    else:
                                        content = raw_content
                            except Exception as e:
                                logger.error(f"Error processing uploaded document {file_path}: {e}")

                    elif file_type == "static":
                        # Static file (image) - read from storage
                        stored_filename = file_info.get("stored_filename", "")
                        profile_file_id = file_info.get("profile_file_id", "")

                        if stored_filename and profile_file_id:
                            try:
                                profile_file = self.db.query(ProfileFile).filter(
                                    ProfileFile.id == profile_file_id
                                ).first()
                                if profile_file:
                                    raw_content = await file_storage.read_file(
                                        profile_file.profile_id, stored_filename
                                    )

                                    # Inject EXIF if it's an image
                                    if profile_file.mime_type and profile_file.mime_type.startswith("image/"):
                                        content = inject_exif(
                                            raw_content,
                                            camera=None,
                                            location=None,
                                            photo_date=ts,
                                            add_gps_variance=True,
                                            strip_existing=True,
                                        )
                                        logger.debug(f"Injected EXIF into uploaded image {file_path}")
                                    else:
                                        content = raw_content
                            except Exception as e:
                                logger.error(f"Error reading static file {file_path}: {e}")

                    elif file_type == "shortcut":
                        # Shortcut file - regenerate content from target_url
                        target_url = file_info.get("target_url", "")
                        if target_url and file_path:
                            # Determine shortcut type from file extension
                            if file_path.endswith('.url'):
                                content = shortcut_generator.generate_windows_url(target_url)
                            elif file_path.endswith('.webloc'):
                                content = shortcut_generator.generate_macos_webloc(target_url)

                    elif file_type == "template":
                        # Custom template - replace placeholders
                        custom_content = file_info.get("custom_content", "")
                        token_urls = file_info.get("token_urls", {})

                        if custom_content:
                            processed_content = custom_content

                            # Replace new format placeholders {canary_token-TYPE}
                            # Use short URLs when available (URL shortening enabled)
                            for placeholder_type, original_url in token_urls.items():
                                if placeholder_type == "_legacy":
                                    # Handle legacy {canary_url} placeholder
                                    processed_content = processed_content.replace("{canary_url}", original_url or "")
                                else:
                                    # Look up token to check for short URL
                                    url_to_use = original_url
                                    if original_url:
                                        token_obj = self.db.query(Token).filter(
                                            Token.drive_id == drive.id,
                                            Token.url == original_url
                                        ).first()
                                        if token_obj and token_obj.short_urls:
                                            url_to_use = token_obj.short_urls[0].short_url
                                            logger.info(f"Using short URL for {placeholder_type} in {file_path}: {url_to_use}")

                                    # Handle new {canary_token-TYPE} placeholders
                                    placeholder = f"{{canary_token-{placeholder_type}}}"
                                    processed_content = processed_content.replace(placeholder, url_to_use or "")

                            # Replace other placeholders
                            processed_content = processed_content.replace("{drive_code}", drive.unique_code)

                            # Handle explicit {short_url} placeholder (for backwards compatibility)
                            short_url_value = ""
                            if "{short_url}" in processed_content:
                                # Find short URLs for any token in this file
                                for placeholder_type, original_url in token_urls.items():
                                    if placeholder_type == "_legacy":
                                        continue
                                    token_obj = self.db.query(Token).filter(
                                        Token.drive_id == drive.id,
                                        Token.url == original_url
                                    ).first()
                                    if token_obj and token_obj.short_urls:
                                        short_url_value = token_obj.short_urls[0].short_url
                                        break

                                # Fallback: use the first token URL if no short URL
                                if not short_url_value and token_urls:
                                    first_url = next((v for k, v in token_urls.items() if k != "_legacy" and v), None)
                                    if first_url:
                                        short_url_value = first_url

                            processed_content = processed_content.replace("{short_url}", short_url_value)

                            content = processed_content.encode('utf-8')

                    elif file_type == "custom_content":
                        # Custom content file from profile wizard - replace placeholders
                        custom_content = file_info.get("custom_content", "")
                        token_urls = file_info.get("token_urls", {})

                        if custom_content:
                            processed_content = custom_content

                            # Replace new format placeholders {canary_token-TYPE}
                            # Use short URLs when available (URL shortening enabled)
                            for placeholder_type, original_url in token_urls.items():
                                if placeholder_type == "_legacy":
                                    # Handle legacy {canary_url} placeholder
                                    processed_content = processed_content.replace("{canary_url}", original_url or "")
                                else:
                                    # Look up token to check for short URL
                                    url_to_use = original_url
                                    if original_url:
                                        token_obj = self.db.query(Token).filter(
                                            Token.drive_id == drive.id,
                                            Token.url == original_url
                                        ).first()
                                        if token_obj and token_obj.short_urls:
                                            url_to_use = token_obj.short_urls[0].short_url
                                            logger.info(f"Using short URL for {placeholder_type} in {file_path}: {url_to_use}")

                                    # Handle new {canary_token-TYPE} placeholders
                                    placeholder = f"{{canary_token-{placeholder_type}}}"
                                    processed_content = processed_content.replace(placeholder, url_to_use or "")

                            # Replace other placeholders
                            processed_content = processed_content.replace("{drive_code}", drive.unique_code)

                            # Handle explicit {short_url} placeholder (for backwards compatibility)
                            short_url_value = ""
                            if "{short_url}" in processed_content:
                                # Find short URLs for any token in this file
                                for placeholder_type, original_url in token_urls.items():
                                    if placeholder_type == "_legacy":
                                        continue
                                    token_obj = self.db.query(Token).filter(
                                        Token.drive_id == drive.id,
                                        Token.url == original_url
                                    ).first()
                                    if token_obj and token_obj.short_urls:
                                        short_url_value = token_obj.short_urls[0].short_url
                                        break

                                # Fallback: use the first token URL if no short URL
                                if not short_url_value and token_urls:
                                    first_url = next((v for k, v in token_urls.items() if k != "_legacy" and v), None)
                                    if first_url:
                                        short_url_value = first_url

                            processed_content = processed_content.replace("{short_url}", short_url_value)

                            content = processed_content.encode('utf-8')
                            logger.info(f"Processed custom content file {file_path} with {len(token_urls)} token(s)")

                    # Write content with realistic timestamp
                    if content:
                        zinfo = zipfile.ZipInfo(
                            filename=file_path,
                            date_time=TimestampService.format_for_zip(ts)
                        )
                        zinfo.compress_type = zipfile.ZIP_DEFLATED
                        zf.writestr(zinfo, content)

                except Exception as e:
                    logger.error(f"Error adding file {file_path} to ZIP: {e}")
                    continue

            # Add junk files for realism
            if profile_scenario:
                junk_files = get_junk_files_for_scenario(
                    profile_scenario,
                    include_system_files=True
                )
                for junk_file in junk_files:
                    try:
                        # Generate timestamp for junk file (older than main files)
                        junk_ts = TimestampService.generate_timestamps(scenario_type)["created"]

                        junk_zinfo = zipfile.ZipInfo(
                            filename=junk_file.path,
                            date_time=TimestampService.format_for_zip(junk_ts)
                        )

                        # Write content (empty for binary system files)
                        content = junk_file.content.encode('utf-8') if junk_file.content else b''
                        zf.writestr(junk_zinfo, content)
                        logger.debug(f"Added junk file: {junk_file.path}")

                    except Exception as e:
                        logger.warning(f"Failed to add junk file {junk_file.path}: {e}")

            # Add README with recent timestamp
            readme_ts = TimestampService.generate_timestamps(scenario_type)["modified"]
            readme_content = self._create_readme(drive)
            readme_zinfo = zipfile.ZipInfo(
                filename="_README.txt",
                date_time=TimestampService.format_for_zip(readme_ts)
            )
            zf.writestr(readme_zinfo, readme_content)

        zip_buffer.seek(0)
        return zip_buffer.read()

    def _create_desktop_ini(self, hostname: str) -> str:
        """Create desktop.ini content for folder token."""
        return f"""[.ShellClassInfo]
IconResource=\\\\{hostname}\\icon.ico,0
"""

    def _create_aws_credentials(
        self,
        access_key_id: Optional[str],
        secret_access_key: Optional[str],
    ) -> str:
        """Create AWS credentials file content."""
        return f"""[default]
aws_access_key_id = {access_key_id or 'AKIAXXXXXXXXXXXXXXXX'}
aws_secret_access_key = {secret_access_key or 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}
"""

    def _create_readme(self, drive: Drive) -> str:
        """Create README content for the drive."""
        return f"""USB Drive: {drive.unique_code}
Created: {drive.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Profile: {drive.profile.name if drive.profile else 'Custom'}

This drive contains files for security testing purposes.
"""
