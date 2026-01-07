"""Email notification service using Mailgun."""

import httpx
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications via Mailgun."""

    def __init__(self):
        self.api_key = os.environ.get("MAILGUN_API_KEY", "")
        self.domain = os.environ.get("MAILGUN_DOMAIN", "")
        self.from_address = os.environ.get(
            "MAILGUN_FROM_ADDRESS",
            f"USB Drop Alerts <alerts@{self.domain}>"
        )
        self.base_url = os.environ.get(
            "MAILGUN_BASE_URL",
            "https://api.mailgun.net/v3"
        )
        self.timeout = 10.0

    @property
    def is_configured(self) -> bool:
        """Check if Mailgun is properly configured."""
        return bool(self.api_key and self.domain)

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
    ) -> bool:
        """
        Send an email via Mailgun.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            text: Plain text body
            html: HTML body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Mailgun not configured, skipping email")
            return False

        if isinstance(to, list):
            to = ", ".join(to)

        data = {
            "from": self.from_address,
            "to": to,
            "subject": subject,
        }

        if text:
            data["text"] = text
        if html:
            data["html"] = html

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{self.domain}/messages",
                    auth=("api", self.api_key),
                    data=data,
                )
                response.raise_for_status()
                logger.info(f"Email sent to {to}: {subject}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Mailgun HTTP error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    async def send_trigger_alert(
        self,
        to: str | list[str],
        drive_code: str,
        token_type: str,
        source_ip: str,
        location: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Send a token trigger alert email.

        Args:
            to: Recipient email address(es)
            drive_code: The triggered drive's unique code
            token_type: Type of token that was triggered
            source_ip: IP address that triggered the token
            location: Geographic location (optional)
            timestamp: When the trigger occurred (optional)

        Returns:
            True if sent successfully
        """
        subject = f"🚨 USB Token Triggered: {drive_code}"

        text = f"""USB Drop Token Triggered!

Drive Code: {drive_code}
Token Type: {token_type}
Source IP: {source_ip}
Location: {location or 'Unknown'}
Time: {timestamp or 'Just now'}

View details in the Campaign Manager dashboard.
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
        .detail {{ margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }}
        .label {{ color: #666; font-size: 12px; text-transform: uppercase; }}
        .value {{ font-size: 16px; font-weight: 600; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🚨 Token Triggered</h1>
            <p style="margin: 5px 0 0 0;">A USB drop token has been activated</p>
        </div>
        <div class="content">
            <div class="detail">
                <div class="label">Drive Code</div>
                <div class="value">{drive_code}</div>
            </div>
            <div class="detail">
                <div class="label">Token Type</div>
                <div class="value">{token_type}</div>
            </div>
            <div class="detail">
                <div class="label">Source IP</div>
                <div class="value">{source_ip}</div>
            </div>
            <div class="detail">
                <div class="label">Location</div>
                <div class="value">{location or 'Unknown'}</div>
            </div>
            <div class="detail">
                <div class="label">Triggered At</div>
                <div class="value">{timestamp or 'Just now'}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

        return await self.send_email(to, subject, text=text, html=html)

    async def send_daily_summary(
        self,
        to: str | list[str],
        campaign_name: str,
        total_triggers: int,
        new_triggers: int,
        top_drives: list[dict],
    ) -> bool:
        """
        Send a daily campaign summary email.

        Args:
            to: Recipient email address(es)
            campaign_name: Name of the campaign
            total_triggers: Total trigger count
            new_triggers: New triggers in last 24 hours
            top_drives: List of most active drives

        Returns:
            True if sent successfully
        """
        subject = f"📊 Daily Summary: {campaign_name}"

        drives_text = "\n".join([
            f"  - {d['code']}: {d['count']} triggers"
            for d in top_drives[:5]
        ]) or "  No triggers yet"

        text = f"""Daily Campaign Summary: {campaign_name}

Total Triggers: {total_triggers}
New (24h): {new_triggers}

Top Active Drives:
{drives_text}

View full report in the Campaign Manager dashboard.
"""

        return await self.send_email(to, subject, text=text)


# Singleton instance
email_service = EmailService()
