"""Settings router - system configuration and Shlink management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import socket
import asyncio
import httpx

from app.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.routers.auth import get_current_user, get_current_admin
from app.services.shlink_client import ShlinkClient, ShlinkError
from app.services.caddy_client import CaddyClient
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ShlinkStatus(BaseModel):
    connected: bool
    domain: str
    api_url: str
    error: Optional[str] = None
    short_url_count: Optional[int] = None


class ShlinkConfig(BaseModel):
    domain: str
    api_url: str
    configured: bool


class ShlinkTestResult(BaseModel):
    success: bool
    test_url: Optional[str] = None
    short_url: Optional[str] = None
    error: Optional[str] = None


class UrlConfigUpdate(BaseModel):
    enabled: bool = True
    base_slug: str = ""
    suffix_mode: str = "random"
    suffix_length: int = 4


class ProfileUrlConfig(BaseModel):
    id: uuid.UUID
    name: str
    scenario_type: str
    enabled: bool
    url_config: dict

    class Config:
        from_attributes = True


@router.get("/shlink/status", response_model=ShlinkStatus)
async def get_shlink_status(
    current_user: User = Depends(get_current_user),
):
    """Check Shlink connection status."""
    client = ShlinkClient()

    try:
        result = await client.list_short_urls(page=1, items_per_page=1)
        total = result.get("shortUrls", {}).get("pagination", {}).get("totalItems", 0)

        return ShlinkStatus(
            connected=True,
            domain=settings.shlink_default_domain,
            api_url=settings.shlink_url,
            short_url_count=total,
        )
    except Exception as e:
        return ShlinkStatus(
            connected=False,
            domain=settings.shlink_default_domain,
            api_url=settings.shlink_url,
            error=str(e),
        )


@router.get("/shlink/config", response_model=ShlinkConfig)
async def get_shlink_config(
    current_user: User = Depends(get_current_user),
):
    """Get current Shlink configuration."""
    return ShlinkConfig(
        domain=settings.shlink_default_domain,
        api_url=settings.shlink_url,
        configured=bool(settings.shlink_api_key),
    )


@router.post("/shlink/test", response_model=ShlinkTestResult)
async def test_shlink_connection(
    current_user: User = Depends(get_current_admin),
):
    """Test Shlink by creating and deleting a test short URL."""
    client = ShlinkClient()
    test_url = "https://example.com/shlink-connection-test"

    try:
        # Create a test short URL
        result = await client.create_short_url(
            long_url=test_url,
            tags=["test", "connection-test"],
            title="Connection Test (auto-delete)",
        )

        short_code = result.get("shortCode")
        short_url = result.get("shortUrl")

        # Delete the test URL
        if short_code:
            await client.delete_short_url(short_code)

        return ShlinkTestResult(
            success=True,
            test_url=test_url,
            short_url=short_url,
        )
    except ShlinkError as e:
        return ShlinkTestResult(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ShlinkTestResult(
            success=False,
            error=f"Unexpected error: {str(e)}",
        )


@router.get("/url-configs", response_model=list[ProfileUrlConfig])
async def get_all_url_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get URL configurations for all profiles."""
    profiles = db.query(Profile).order_by(Profile.name).all()

    result = []
    for profile in profiles:
        url_config = profile.url_config or {}
        result.append(ProfileUrlConfig(
            id=profile.id,
            name=profile.name,
            scenario_type=profile.scenario_type or "",
            enabled=url_config.get("enabled", False),
            url_config=url_config,
        ))

    return result


@router.put("/url-configs/{profile_id}")
async def update_url_config(
    profile_id: uuid.UUID,
    config: UrlConfigUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update URL configuration for a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update url_config
    profile.url_config = {
        "enabled": config.enabled,
        "base_slug": config.base_slug,
        "suffix_mode": config.suffix_mode,
        "suffix_length": config.suffix_length,
    }

    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "name": profile.name,
        "url_config": profile.url_config,
    }


@router.put("/url-configs/bulk")
async def bulk_update_url_configs(
    updates: list[dict],
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Bulk update URL configurations for multiple profiles."""
    updated = []

    for update in updates:
        profile_id = update.get("id")
        if not profile_id:
            continue

        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            continue

        # Update url_config
        profile.url_config = {
            "enabled": update.get("enabled", False),
            "base_slug": update.get("base_slug", ""),
            "suffix_mode": update.get("suffix_mode", "random"),
            "suffix_length": update.get("suffix_length", 4),
        }
        updated.append(str(profile.id))

    db.commit()

    return {"updated": updated, "count": len(updated)}


# =============================================================================
# Domain Management
# =============================================================================

class DomainInfo(BaseModel):
    domain: str
    is_default: bool
    base_url_redirect: Optional[str] = None
    regular_404_redirect: Optional[str] = None
    invalid_short_url_redirect: Optional[str] = None


class DomainListResponse(BaseModel):
    domains: list[DomainInfo]
    default_domain: str


class DNSCheckResult(BaseModel):
    domain: str
    resolves: bool
    ip_addresses: list[str] = []
    reachable: bool
    https_works: bool
    error: Optional[str] = None


class AddDomainRequest(BaseModel):
    domain: str


class ConfigureDomainRequest(BaseModel):
    domain: str
    base_url_redirect: Optional[str] = None
    regular_404_redirect: Optional[str] = None
    invalid_short_url_redirect: Optional[str] = None


@router.get("/shlink/domains", response_model=DomainListResponse)
async def list_shlink_domains(
    current_user: User = Depends(get_current_user),
):
    """List all domains configured in Shlink."""
    client = ShlinkClient()

    try:
        result = await client.list_domains()
        domains_data = result.get("domains", {}).get("data", [])

        domains = []
        default_domain = settings.shlink_default_domain

        for d in domains_data:
            redirects = d.get("redirects", {}) or {}
            domain_info = DomainInfo(
                domain=d.get("domain", ""),
                is_default=d.get("isDefault", False),
                base_url_redirect=redirects.get("baseUrlRedirect"),
                regular_404_redirect=redirects.get("regular404Redirect"),
                invalid_short_url_redirect=redirects.get("invalidShortUrlRedirect"),
            )
            domains.append(domain_info)

            if d.get("isDefault"):
                default_domain = d.get("domain", default_domain)

        return DomainListResponse(domains=domains, default_domain=default_domain)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list domains: {str(e)}")


@router.post("/shlink/domains")
async def add_shlink_domain(
    request: AddDomainRequest,
    current_user: User = Depends(get_current_admin),
):
    """Add a new domain to Shlink."""
    client = ShlinkClient()

    try:
        result = await client.register_domain(request.domain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add domain: {str(e)}")


@router.patch("/shlink/domains/redirects")
async def configure_domain_redirects(
    request: ConfigureDomainRequest,
    current_user: User = Depends(get_current_admin),
):
    """Configure redirects for a domain."""
    client = ShlinkClient()

    try:
        result = await client.configure_domain_redirects(
            domain=request.domain,
            base_url_redirect=request.base_url_redirect,
            regular_404_redirect=request.regular_404_redirect,
            invalid_short_url_redirect=request.invalid_short_url_redirect,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure domain: {str(e)}")


@router.post("/shlink/domains/verify-dns", response_model=DNSCheckResult)
async def verify_domain_dns(
    request: AddDomainRequest,
    current_user: User = Depends(get_current_admin),
):
    """Verify DNS configuration for a domain."""
    domain = request.domain.strip().lower()

    result = DNSCheckResult(
        domain=domain,
        resolves=False,
        reachable=False,
        https_works=False,
    )

    # Check DNS resolution
    try:
        loop = asyncio.get_event_loop()
        ip_addresses = await loop.run_in_executor(
            None, lambda: socket.gethostbyname_ex(domain)[2]
        )
        result.resolves = True
        result.ip_addresses = ip_addresses
    except socket.gaierror as e:
        result.error = f"DNS resolution failed: {str(e)}"
        return result
    except Exception as e:
        result.error = f"DNS check error: {str(e)}"
        return result

    # Check HTTPS reachability
    # Note: When running inside Docker, hairpin NAT issues may cause HTTPS to fail
    # even when the domain works correctly from external clients
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
            response = await client.get(f"https://{domain}/", headers={"User-Agent": "DNS-Verify/1.0"})
            result.https_works = True
            result.reachable = True
    except httpx.ConnectError as e:
        # Check if it's an SSL/hairpin NAT issue (common when verifying from inside Docker)
        error_str = str(e).lower()
        if "ssl" in error_str or "tls" in error_str:
            # This is likely a hairpin NAT issue - DNS works, so domain is probably fine
            result.reachable = True
            result.https_works = False
            result.error = "HTTPS verification failed from server (hairpin NAT) - domain likely works for external users"
        else:
            result.error = "HTTPS connection failed - check SSL certificate"
    except httpx.TimeoutException:
        result.error = "Connection timed out"
    except Exception as e:
        # Try HTTP as fallback
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(f"http://{domain}/", headers={"User-Agent": "DNS-Verify/1.0"})
                result.reachable = True
                result.error = "HTTP works but HTTPS failed - SSL certificate may be missing"
        except:
            result.error = f"Connection failed: {str(e)}"

    return result


# =============================================================================
# Caddy Reverse Proxy Management
# =============================================================================

class CaddyStatus(BaseModel):
    healthy: bool
    admin_url: str
    caddyfile_path: str
    shlink_domains: list[str] = []
    error: Optional[str] = None


class CaddyDomainRequest(BaseModel):
    domain: str


class CaddyDomainResult(BaseModel):
    success: bool
    domain: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


@router.get("/caddy/status", response_model=CaddyStatus)
async def get_caddy_status(
    current_user: User = Depends(get_current_user),
):
    """Get Caddy reverse proxy status."""
    caddy = CaddyClient()

    health = await caddy.health_check()
    shlink_domains = caddy.list_shlink_domains()

    return CaddyStatus(
        healthy=health.get("healthy", False),
        admin_url=settings.caddy_admin_url,
        caddyfile_path=settings.caddyfile_path,
        shlink_domains=shlink_domains,
        error=health.get("error"),
    )


@router.post("/caddy/domains", response_model=CaddyDomainResult)
async def add_caddy_domain(
    request: CaddyDomainRequest,
    current_user: User = Depends(get_current_admin),
):
    """Add a new Shlink domain to Caddy configuration."""
    caddy = CaddyClient()

    result = await caddy.add_shlink_domain(request.domain)

    return CaddyDomainResult(
        success=result.get("success", False),
        domain=result.get("domain"),
        message=result.get("message"),
        error=result.get("error"),
    )


@router.delete("/caddy/domains/{domain}", response_model=CaddyDomainResult)
async def remove_caddy_domain(
    domain: str,
    current_user: User = Depends(get_current_admin),
):
    """Remove a Shlink domain from Caddy configuration."""
    caddy = CaddyClient()

    result = await caddy.remove_shlink_domain(domain)

    return CaddyDomainResult(
        success=result.get("success", False),
        domain=result.get("domain"),
        message=result.get("message"),
        error=result.get("error"),
    )


@router.post("/caddy/reload")
async def reload_caddy(
    current_user: User = Depends(get_current_admin),
):
    """Reload Caddy configuration."""
    caddy = CaddyClient()

    result = await caddy.reload_config()

    return result


@router.post("/shlink/domains/full-setup", response_model=CaddyDomainResult)
async def full_domain_setup(
    request: AddDomainRequest,
    current_user: User = Depends(get_current_admin),
):
    """
    Full domain setup: Add domain to both Caddy and Shlink.

    This endpoint:
    1. Adds the domain to Caddy configuration
    2. Reloads Caddy to provision SSL certificate
    3. Registers the domain with Shlink
    """
    domain = request.domain.strip().lower()

    # Step 1: Add to Caddy
    caddy = CaddyClient()
    caddy_result = await caddy.add_shlink_domain(domain)

    if not caddy_result.get("success"):
        return CaddyDomainResult(
            success=False,
            domain=domain,
            error=f"Caddy setup failed: {caddy_result.get('error')}",
        )

    # Step 2: Register with Shlink
    shlink = ShlinkClient()
    try:
        shlink_result = await shlink.register_domain(domain)

        if not shlink_result.get("success"):
            # Caddy succeeded but Shlink failed - still report success
            # since the domain is usable, just not registered in Shlink yet
            return CaddyDomainResult(
                success=True,
                domain=domain,
                message=f"Domain {domain} added to Caddy. Shlink registration: {shlink_result.get('error', 'pending')}",
            )
    except Exception as e:
        # Shlink registration is optional, Caddy setup is the important part
        return CaddyDomainResult(
            success=True,
            domain=domain,
            message=f"Domain {domain} added to Caddy. Shlink registration will happen on first use.",
        )

    return CaddyDomainResult(
        success=True,
        domain=domain,
        message=f"Domain {domain} fully configured with Caddy and Shlink",
    )
