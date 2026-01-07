"""Geolocation service for IP lookups using IPinfo."""

import httpx
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class GeoService:
    """Service for IP geolocation lookups using IPinfo API."""

    def __init__(self):
        self.api_token = os.environ.get("IPINFO_TOKEN", "")
        self.api_url = "https://ipinfo.io"
        self.timeout = 5.0

    async def lookup(self, ip_address: str) -> dict:
        """
        Look up geolocation data for an IP address using IPinfo.

        Returns:
            Dictionary with location data or empty dict on failure
        """
        if not ip_address or ip_address in ["127.0.0.1", "::1", "localhost"]:
            return {}

        try:
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/{ip_address}/json",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                # Parse location (format: "lat,lon")
                loc = data.get("loc", "")
                lat, lon = None, None
                if loc and "," in loc:
                    try:
                        lat, lon = map(float, loc.split(","))
                    except ValueError:
                        pass

                return {
                    "country": data.get("country"),
                    "country_code": data.get("country"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "latitude": lat,
                    "longitude": lon,
                    "isp": data.get("org"),
                    "org": data.get("org"),
                    "postal": data.get("postal"),
                    "timezone": data.get("timezone"),
                    "hostname": data.get("hostname"),
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"IPinfo rate limit exceeded for {ip_address}")
            else:
                logger.error(f"IPinfo HTTP error for {ip_address}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Geo lookup error for {ip_address}: {e}")
            return {}

    async def batch_lookup(self, ip_addresses: list[str]) -> dict[str, dict]:
        """
        Look up geolocation for multiple IP addresses.

        Note: IPinfo has a batch API endpoint for paid plans that could be
        used here for better efficiency.

        Returns:
            Dictionary mapping IP addresses to their geo data
        """
        results = {}
        for ip in ip_addresses:
            results[ip] = await self.lookup(ip)
        return results


# Singleton instance
geo_service = GeoService()
