"""Shlink URL shortener API client."""

import secrets
import httpx
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ShlinkClient:
    """Client for interacting with Shlink URL shortener API."""

    def __init__(self):
        self.server_url = settings.shlink_url.rstrip("/")
        self.api_key = settings.shlink_api_key
        self.default_domain = settings.shlink_default_domain
        self.timeout = 30.0

    def _headers(self) -> dict:
        """Get authorization headers."""
        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def create_short_url(
        self,
        long_url: str,
        custom_slug: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Optional[list[str]] = None,
        title: Optional[str] = None,
        crawlable: bool = False,
        forward_query: bool = True,
    ) -> dict:
        """
        Create a short URL.

        Args:
            long_url: The URL to shorten
            custom_slug: Custom slug for the short URL
            domain: Domain to use (defaults to shlink_default_domain)
            tags: List of tags for organizing short URLs
            title: Title for the short URL
            crawlable: Allow search engines to crawl
            forward_query: Forward query params to long URL

        Returns:
            API response with shortCode, shortUrl, longUrl, etc.
        """
        url = f"{self.server_url}/rest/v3/short-urls"

        payload = {
            "longUrl": long_url,
            "crawlable": crawlable,
            "forwardQuery": forward_query,
        }

        if custom_slug:
            payload["customSlug"] = custom_slug

        if domain:
            payload["domain"] = domain
        else:
            payload["domain"] = self.default_domain

        if tags:
            payload["tags"] = tags

        if title:
            payload["title"] = title

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())

            if response.status_code == 400:
                error_data = response.json()
                # Handle slug already exists error
                if error_data.get("type") == "https://shlink.io/api/error/non-unique-slug":
                    raise SlugExistsError(f"Slug '{custom_slug}' already exists")
                raise ShlinkError(f"Shlink error: {error_data}")

            response.raise_for_status()
            return response.json()

    async def get_short_url(self, short_code: str, domain: Optional[str] = None) -> dict:
        """
        Get details of a short URL.

        Args:
            short_code: The short code
            domain: Domain (required if not default)

        Returns:
            Short URL details
        """
        url = f"{self.server_url}/rest/v3/short-urls/{short_code}"
        params = {}
        if domain:
            params["domain"] = domain

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def delete_short_url(self, short_code: str, domain: Optional[str] = None) -> bool:
        """
        Delete a short URL.

        Args:
            short_code: The short code to delete
            domain: Domain (required if not default)

        Returns:
            True if deleted successfully
        """
        url = f"{self.server_url}/rest/v3/short-urls/{short_code}"
        params = {}
        if domain:
            params["domain"] = domain

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url, params=params, headers=self._headers())
            return response.status_code == 204

    async def list_short_urls(
        self,
        tags: Optional[list[str]] = None,
        page: int = 1,
        items_per_page: int = 100,
    ) -> dict:
        """
        List short URLs with optional filtering.

        Args:
            tags: Filter by tags
            page: Page number
            items_per_page: Items per page

        Returns:
            Paginated list of short URLs
        """
        url = f"{self.server_url}/rest/v3/short-urls"
        params = {
            "page": page,
            "itemsPerPage": items_per_page,
        }
        if tags:
            params["tags[]"] = tags

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def get_visits(self, short_code: str, domain: Optional[str] = None) -> dict:
        """
        Get visit statistics for a short URL.

        Args:
            short_code: The short code
            domain: Domain (required if not default)

        Returns:
            Visit statistics
        """
        url = f"{self.server_url}/rest/v3/short-urls/{short_code}/visits"
        params = {}
        if domain:
            params["domain"] = domain

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def list_domains(self) -> dict:
        """
        List all configured domains.

        Returns:
            Dict with domains data and default redirects
        """
        url = f"{self.server_url}/rest/v3/domains"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def configure_domain_redirects(
        self,
        domain: str,
        base_url_redirect: Optional[str] = None,
        regular_404_redirect: Optional[str] = None,
        invalid_short_url_redirect: Optional[str] = None,
    ) -> dict:
        """
        Configure redirects for a domain.

        Args:
            domain: The domain to configure
            base_url_redirect: URL to redirect when accessing domain root
            regular_404_redirect: URL for 404 errors
            invalid_short_url_redirect: URL for invalid short URLs

        Returns:
            Updated domain configuration
        """
        url = f"{self.server_url}/rest/v3/domains/redirects"

        payload = {"domain": domain}
        if base_url_redirect is not None:
            payload["baseUrlRedirect"] = base_url_redirect
        if regular_404_redirect is not None:
            payload["regular404Redirect"] = regular_404_redirect
        if invalid_short_url_redirect is not None:
            payload["invalidShortUrlRedirect"] = invalid_short_url_redirect

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(url, json=payload, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def register_domain(self, domain: str) -> dict:
        """
        Register a new domain by configuring its redirects.
        This persists the domain in Shlink's domain list.

        Args:
            domain: The domain to register

        Returns:
            Domain registration result
        """
        try:
            # Configure redirects to persist the domain in Shlink
            # This ensures the domain shows up in the domain list
            await self.configure_domain_redirects(
                domain=domain,
                base_url_redirect="https://app.subproject55.com",
            )

            return {"success": True, "domain": domain, "registered": True}
        except Exception as e:
            return {"success": False, "domain": domain, "error": str(e)}

    def generate_random_suffix(self, length: int = 4) -> str:
        """Generate a random alphanumeric suffix."""
        # Use secrets for cryptographically secure random
        alphabet = "abcdefghijkmnopqrstuvwxyz23456789"  # Avoid ambiguous chars: 1, l, 0, o
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_drive_short_url(
        self,
        canary_url: str,
        base_slug: str,
        suffix_mode: str,
        drive_code: str,
        drive_id: str,
        token_id: str,
        suffix_length: int = 4,
        custom_suffix: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> dict:
        """
        Create a short URL for a drive token with appropriate suffix.

        Args:
            canary_url: The CanaryTokens URL to shorten
            base_slug: Base slug from profile (e.g., "hr-docs")
            suffix_mode: One of: random, sequential, drive_code, custom
            drive_code: The drive's unique code (e.g., "USB-A1B2C3")
            drive_id: Drive UUID for tagging
            token_id: Token UUID for tagging
            suffix_length: Length for random suffix (default 4)
            custom_suffix: Custom suffix (for custom mode)
            domain: Override default domain

        Returns:
            Dict with short_url info and generated suffix
        """
        # Generate the suffix based on mode
        if suffix_mode == "random":
            suffix = self.generate_random_suffix(suffix_length)
        elif suffix_mode == "drive_code":
            suffix = drive_code.lower().replace("-", "")
        elif suffix_mode == "custom" and custom_suffix:
            suffix = custom_suffix
        elif suffix_mode == "sequential":
            # For sequential, we'll just use a random suffix and let caller handle numbering
            suffix = self.generate_random_suffix(suffix_length)
        else:
            suffix = self.generate_random_suffix(suffix_length)

        # Build full slug
        full_slug = f"{base_slug}-{suffix}" if base_slug else suffix

        # Tags for organizing
        tags = [f"drive:{drive_id}", f"token:{token_id}"]

        result = await self.create_short_url(
            long_url=canary_url,
            custom_slug=full_slug,
            domain=domain,
            tags=tags,
            title=f"Drive {drive_code} token",
        )

        # Add our generated info to result
        result["generated_suffix"] = suffix
        result["full_slug"] = full_slug
        result["base_slug"] = base_slug
        result["suffix_mode"] = suffix_mode

        return result


class ShlinkError(Exception):
    """General Shlink API error."""
    pass


class SlugExistsError(ShlinkError):
    """Slug already exists error."""
    pass
