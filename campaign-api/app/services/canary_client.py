"""CanaryTokens API client for self-hosted instance."""

import base64
import httpx
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CanaryTokensClient:
    """Client for interacting with self-hosted CanaryTokens API."""

    def __init__(self):
        self.server_url = settings.canary_server.rstrip("/")
        self.factory_auth = settings.factory_auth
        self.timeout = 30.0

    async def create_token(
        self,
        token_type: str,
        memo: str,
        email: str = "alerts@example.com",
        redirect_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create a new Canarytoken.

        Args:
            token_type: Token type (dns, ms_word, ms_excel, web, etc.)
            memo: Description/identifier for the token
            email: Email address for alerts
            redirect_url: URL for redirect tokens
            webhook_url: URL for webhook alerts
            **kwargs: Additional token-specific parameters

        Returns:
            API response with token info including 'token' and 'auth_token'
        """
        url = f"{self.server_url}/generate"

        payload = {
            "type": token_type,
            "memo": memo,
            "email": email,
            "factory_auth": self.factory_auth,
        }

        if redirect_url:
            payload["redirect_url"] = redirect_url

        # Enable webhook alerting if URL provided or use default from settings
        effective_webhook_url = webhook_url or settings.webhook_url
        if effective_webhook_url:
            payload["webhook_url"] = effective_webhook_url

        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                raise Exception(f"CanaryTokens error: {result.get('error_message')}")

            # Normalize response to include canarytoken dict for compatibility
            result["canarytoken"] = {
                "canarytoken": result.get("token", ""),
                "auth_token": result.get("auth_token", ""),
                "hostname": result.get("hostname", ""),
                "url": result.get("token_url", ""),
            }

            return result

    async def download_token(self, token_id: str, auth_token: str = None, fmt: str = None) -> bytes:
        """
        Download a token file (for document-based tokens).

        Args:
            token_id: The canarytoken ID
            auth_token: The auth token from creation response
            fmt: Format type (msword, msexcel, etc.)

        Returns:
            File content as bytes
        """
        # Determine format from token type if not specified
        if fmt is None:
            fmt = "msword"  # Default

        url = f"{self.server_url}/download"
        params = {
            "token": token_id,
            "fmt": fmt,
        }
        if auth_token:
            params["auth"] = auth_token

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, follow_redirects=True)
            response.raise_for_status()
            content = response.content

            # Handle base64 data URLs (used for QR codes)
            if content.startswith(b"data:"):
                try:
                    # Format: data:image/png;base64,<base64_data>
                    header, encoded = content.decode().split(",", 1)
                    content = base64.b64decode(encoded)
                except Exception as e:
                    logger.error(f"Failed to decode base64 data URL: {e}")

            return content

    async def fetch_token(self, token_id: str) -> dict:
        """Fetch details of a Canarytoken."""
        url = f"{self.server_url}/manage"
        params = {
            "token": token_id,
            "factory_auth": self.factory_auth,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def delete_token(self, token_id: str, auth_token: str) -> dict:
        """Delete a Canarytoken."""
        url = f"{self.server_url}/manage"

        payload = {
            "token": token_id,
            "auth": auth_token,
            "delete": "1",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def create_dns_token(self, memo: str) -> dict:
        """Create a DNS token."""
        return await self.create_token(token_type="dns", memo=memo)

    async def create_word_token(self, memo: str) -> dict:
        """Create a Word document token."""
        return await self.create_token(token_type="ms_word", memo=memo)

    async def create_excel_token(self, memo: str) -> dict:
        """Create an Excel document token."""
        return await self.create_token(token_type="ms_excel", memo=memo)

    async def create_pdf_token(self, memo: str) -> dict:
        """Create a PDF token (requires Adobe Reader)."""
        return await self.create_token(token_type="adobe_pdf", memo=memo)

    async def create_folder_token(self, memo: str) -> dict:
        """Create a Windows folder token."""
        return await self.create_token(token_type="windows_dir", memo=memo)

    async def create_aws_token(self, memo: str) -> dict:
        """Create AWS credentials token."""
        return await self.create_token(token_type="aws_keys", memo=memo)

    async def create_qr_token(self, memo: str, redirect_url: str) -> dict:
        """Create a QR code token."""
        return await self.create_token(
            token_type="qr_code",
            memo=memo,
            redirect_url=redirect_url,
        )

    async def create_web_token(self, memo: str, redirect_url: Optional[str] = None) -> dict:
        """Create a web bug token. Uses slow_redirect type if redirect_url is provided."""
        # Use slow_redirect for tokens with a landing page, plain web for tracking-only
        token_type = "slow_redirect" if redirect_url else "web"
        return await self.create_token(
            token_type=token_type,
            memo=memo,
            redirect_url=redirect_url,
        )
