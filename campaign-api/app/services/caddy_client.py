"""Caddy reverse proxy management client."""

import httpx
import re
import os
from datetime import datetime
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CaddyClient:
    """Client for managing Caddy reverse proxy configuration."""

    def __init__(self):
        self.admin_url = settings.caddy_admin_url.rstrip("/")
        self.caddyfile_path = settings.caddyfile_path
        self.timeout = 30.0

    async def health_check(self) -> dict:
        """Check if Caddy admin API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.admin_url}/config/")
                return {
                    "healthy": response.status_code == 200,
                    "status_code": response.status_code,
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }

    async def reload_config(self) -> dict:
        """Reload Caddy configuration from Caddyfile."""
        try:
            # Read the Caddyfile
            with open(self.caddyfile_path, "r") as f:
                caddyfile_content = f.read()

            # Use Caddy's /load endpoint with Caddyfile adapter
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.admin_url}/load",
                    content=caddyfile_content,
                    headers={"Content-Type": "text/caddyfile"},
                )

                if response.status_code == 200:
                    return {"success": True, "message": "Configuration reloaded"}
                else:
                    return {
                        "success": False,
                        "error": f"Reload failed: {response.status_code} - {response.text}",
                    }
        except Exception as e:
            logger.error(f"Failed to reload Caddy config: {e}")
            return {"success": False, "error": str(e)}

    def _validate_domain(self, domain: str) -> bool:
        """Validate domain format."""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))

    def _domain_exists(self, domain: str) -> bool:
        """Check if domain already exists in Caddyfile."""
        try:
            with open(self.caddyfile_path, "r") as f:
                content = f.read()
            # Look for domain block
            pattern = rf'^{re.escape(domain)}\s*\{{'
            return bool(re.search(pattern, content, re.MULTILINE))
        except Exception:
            return False

    def _backup_caddyfile(self) -> str:
        """Create a backup of the Caddyfile."""
        backup_path = f"{self.caddyfile_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            with open(self.caddyfile_path, "r") as f:
                content = f.read()
            with open(backup_path, "w") as f:
                f.write(content)
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup Caddyfile: {e}")
            raise

    async def add_shlink_domain(self, domain: str) -> dict:
        """
        Add a new Shlink domain to the Caddyfile and reload Caddy.

        Args:
            domain: The domain to add (e.g., short.example.com)

        Returns:
            Dict with success status and any error messages
        """
        domain = domain.strip().lower()

        # Validate domain
        if not self._validate_domain(domain):
            return {"success": False, "error": "Invalid domain format"}

        # Check if already exists
        if self._domain_exists(domain):
            return {"success": False, "error": f"Domain '{domain}' already exists in Caddyfile"}

        try:
            # Backup current config
            backup_path = self._backup_caddyfile()
            logger.info(f"Created Caddyfile backup: {backup_path}")

            # Read current Caddyfile
            with open(self.caddyfile_path, "r") as f:
                content = f.read()

            # Create new domain configuration
            new_config = f"""
# Shlink domain: {domain} (added {datetime.now().strftime('%Y-%m-%d')})
{domain} {{
    reverse_proxy shlink:8080
}}
"""

            # Find where to insert (before wildcard section or at end)
            wildcard_pattern = r'\n# =+\n# Wildcard'
            match = re.search(wildcard_pattern, content)

            if match:
                # Insert before wildcard section
                insert_pos = match.start()
                new_content = content[:insert_pos] + new_config + content[insert_pos:]
            else:
                # Append to end
                new_content = content + new_config

            # Write updated Caddyfile
            with open(self.caddyfile_path, "w") as f:
                f.write(new_content)

            logger.info(f"Added domain {domain} to Caddyfile")

            # Reload Caddy
            reload_result = await self.reload_config()

            if not reload_result.get("success"):
                # Restore backup on failure
                logger.error(f"Caddy reload failed, restoring backup")
                with open(backup_path, "r") as f:
                    backup_content = f.read()
                with open(self.caddyfile_path, "w") as f:
                    f.write(backup_content)
                return {
                    "success": False,
                    "error": f"Caddy reload failed: {reload_result.get('error')}. Configuration restored.",
                }

            return {
                "success": True,
                "domain": domain,
                "message": f"Domain {domain} added and SSL certificate will be provisioned automatically",
            }

        except Exception as e:
            logger.error(f"Failed to add domain {domain}: {e}")
            return {"success": False, "error": str(e)}

    async def remove_shlink_domain(self, domain: str) -> dict:
        """
        Remove a Shlink domain from the Caddyfile and reload Caddy.

        Args:
            domain: The domain to remove

        Returns:
            Dict with success status and any error messages
        """
        domain = domain.strip().lower()

        if not self._domain_exists(domain):
            return {"success": False, "error": f"Domain '{domain}' not found in Caddyfile"}

        try:
            # Backup current config
            backup_path = self._backup_caddyfile()

            # Read current Caddyfile
            with open(self.caddyfile_path, "r") as f:
                content = f.read()

            # Remove the domain block (including comment line above)
            # Pattern matches:
            # # Shlink domain: example.com (added YYYY-MM-DD)
            # example.com {
            #     reverse_proxy shlink:8080
            # }
            pattern = rf'\n?# Shlink domain: {re.escape(domain)}[^\n]*\n{re.escape(domain)} \{{\n[^}}]+\}}\n?'
            new_content = re.sub(pattern, '\n', content)

            # If the comment pattern didn't match, try without comment
            if new_content == content:
                pattern = rf'\n?{re.escape(domain)} \{{\n[^}}]+\}}\n?'
                new_content = re.sub(pattern, '\n', content)

            # Write updated Caddyfile
            with open(self.caddyfile_path, "w") as f:
                f.write(new_content)

            # Reload Caddy
            reload_result = await self.reload_config()

            if not reload_result.get("success"):
                # Restore backup on failure
                with open(backup_path, "r") as f:
                    backup_content = f.read()
                with open(self.caddyfile_path, "w") as f:
                    f.write(backup_content)
                return {
                    "success": False,
                    "error": f"Caddy reload failed: {reload_result.get('error')}. Configuration restored.",
                }

            return {
                "success": True,
                "domain": domain,
                "message": f"Domain {domain} removed successfully",
            }

        except Exception as e:
            logger.error(f"Failed to remove domain {domain}: {e}")
            return {"success": False, "error": str(e)}

    def list_shlink_domains(self) -> list[str]:
        """List all Shlink domains from the Caddyfile."""
        try:
            with open(self.caddyfile_path, "r") as f:
                content = f.read()

            # Find all domains that proxy to shlink
            # Pattern: domain.com {\n    reverse_proxy shlink:8080
            pattern = r'^([a-zA-Z0-9][a-zA-Z0-9.-]+)\s*\{\s*\n\s*reverse_proxy\s+shlink:8080'
            matches = re.findall(pattern, content, re.MULTILINE)

            return matches
        except Exception as e:
            logger.error(f"Failed to list Shlink domains: {e}")
            return []


class CaddyError(Exception):
    """Caddy management error."""
    pass
