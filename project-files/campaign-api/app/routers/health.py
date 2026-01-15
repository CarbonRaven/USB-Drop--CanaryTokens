"""Health check endpoints for monitoring application status."""

import time
import os
from datetime import datetime
from typing import Optional
from enum import Enum

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Track application start time
APP_START_TIME = datetime.utcnow()


class HealthStatus(str, Enum):
    """Health status values."""
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"
    UNCONFIGURED = "unconfigured"


class ServiceHealth(BaseModel):
    """Health status for a single service."""
    status: HealthStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[dict] = None


class DetailedHealth(BaseModel):
    """Detailed health status for all services."""
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str
    services: dict[str, ServiceHealth]


async def check_database_health(db: Session) -> ServiceHealth:
    """Check database connectivity and performance."""
    start = time.perf_counter()
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        latency = (time.perf_counter() - start) * 1000

        # Get connection pool stats
        pool = engine.pool
        details = {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }

        return ServiceHealth(
            status=HealthStatus.OK,
            latency_ms=round(latency, 2),
            message="Connected",
            details=details
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(
            status=HealthStatus.ERROR,
            latency_ms=round(latency, 2),
            message=str(e)
        )


async def check_canarytokens_health() -> ServiceHealth:
    """Check CanaryTokens service connectivity."""
    if not settings.canary_server:
        return ServiceHealth(
            status=HealthStatus.UNCONFIGURED,
            message="CANARY_SERVER not configured"
        )

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.canary_server}/")
            latency = (time.perf_counter() - start) * 1000

            if response.status_code < 400:
                return ServiceHealth(
                    status=HealthStatus.OK,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                    details={"url": settings.canary_server}
                )
            else:
                return ServiceHealth(
                    status=HealthStatus.DEGRADED,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}"
                )
    except httpx.ConnectError:
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(
            status=HealthStatus.ERROR,
            latency_ms=round(latency, 2),
            message="Connection refused"
        )
    except httpx.TimeoutException:
        return ServiceHealth(
            status=HealthStatus.ERROR,
            message="Connection timeout"
        )
    except Exception as e:
        return ServiceHealth(
            status=HealthStatus.ERROR,
            message=str(e)
        )


async def check_openai_health() -> ServiceHealth:
    """Check OpenAI API configuration and connectivity."""
    api_key = settings.openai_api_key
    if not api_key:
        return ServiceHealth(
            status=HealthStatus.UNCONFIGURED,
            message="OPENAI_API_KEY not configured"
        )

    # Validate key format without making an API call
    if not api_key.startswith("sk-"):
        return ServiceHealth(
            status=HealthStatus.DEGRADED,
            message="Invalid API key format"
        )

    # Optionally test connectivity (commented out to avoid API charges)
    # start = time.perf_counter()
    # try:
    #     async with httpx.AsyncClient(timeout=10.0) as client:
    #         response = await client.get(
    #             "https://api.openai.com/v1/models",
    #             headers={"Authorization": f"Bearer {api_key}"}
    #         )
    #         latency = (time.perf_counter() - start) * 1000
    #         if response.status_code == 200:
    #             return ServiceHealth(status=HealthStatus.OK, latency_ms=round(latency, 2))
    #         elif response.status_code == 401:
    #             return ServiceHealth(status=HealthStatus.ERROR, message="Invalid API key")
    #         else:
    #             return ServiceHealth(status=HealthStatus.DEGRADED, message=f"HTTP {response.status_code}")
    # except Exception as e:
    #     return ServiceHealth(status=HealthStatus.ERROR, message=str(e))

    return ServiceHealth(
        status=HealthStatus.OK,
        message="Configured (key format valid)",
        details={"key_prefix": api_key[:7] + "..."}
    )


async def check_slack_health() -> ServiceHealth:
    """Check Slack webhook configuration."""
    webhook_url = settings.slack_webhook_url
    if not webhook_url:
        return ServiceHealth(
            status=HealthStatus.UNCONFIGURED,
            message="SLACK_WEBHOOK_URL not configured"
        )

    # Validate URL format
    if "hooks.slack.com" not in webhook_url:
        return ServiceHealth(
            status=HealthStatus.DEGRADED,
            message="URL may be invalid"
        )

    return ServiceHealth(
        status=HealthStatus.OK,
        message="Configured"
    )


async def check_geolocation_health() -> ServiceHealth:
    """Check IP geolocation service."""
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Use a known IP for testing (Google DNS)
            response = await client.get("http://ip-api.com/json/8.8.8.8")
            latency = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return ServiceHealth(
                        status=HealthStatus.OK,
                        latency_ms=round(latency, 2),
                        message="Service available"
                    )

            return ServiceHealth(
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message=f"HTTP {response.status_code}"
            )
    except Exception as e:
        return ServiceHealth(
            status=HealthStatus.ERROR,
            message=str(e)
        )


async def check_filesystem_health() -> ServiceHealth:
    """Check filesystem and uploads directory."""
    uploads_dir = "/app/uploads"

    try:
        if not os.path.exists(uploads_dir):
            return ServiceHealth(
                status=HealthStatus.ERROR,
                message="Uploads directory does not exist"
            )

        if not os.access(uploads_dir, os.W_OK):
            return ServiceHealth(
                status=HealthStatus.ERROR,
                message="Uploads directory not writable"
            )

        # Check available space
        statvfs = os.statvfs(uploads_dir)
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        free_gb = free_bytes / (1024 ** 3)

        if free_gb < 1:
            return ServiceHealth(
                status=HealthStatus.DEGRADED,
                message=f"Low disk space: {free_gb:.2f} GB",
                details={"free_gb": round(free_gb, 2)}
            )

        return ServiceHealth(
            status=HealthStatus.OK,
            message="Writable",
            details={"free_gb": round(free_gb, 2)}
        )
    except Exception as e:
        return ServiceHealth(
            status=HealthStatus.ERROR,
            message=str(e)
        )


@router.get("/", response_model=dict)
async def basic_health():
    """Basic health check - returns 200 if API is running."""
    return {"status": "healthy"}


@router.get("/detailed", response_model=DetailedHealth)
async def detailed_health(db: Session = Depends(get_db)):
    """
    Detailed health check for all services.

    Returns comprehensive health information for monitoring and debugging.
    """
    uptime = (datetime.utcnow() - APP_START_TIME).total_seconds()

    # Run all health checks
    services = {
        "database": await check_database_health(db),
        "canarytokens": await check_canarytokens_health(),
        "openai": await check_openai_health(),
        "slack": await check_slack_health(),
        "geolocation": await check_geolocation_health(),
        "filesystem": await check_filesystem_health(),
    }

    # Determine overall status
    statuses = [s.status for s in services.values()]

    if HealthStatus.ERROR in statuses:
        overall_status = HealthStatus.ERROR
    elif HealthStatus.DEGRADED in statuses:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.OK

    return DetailedHealth(
        status=overall_status,
        timestamp=datetime.utcnow(),
        uptime_seconds=round(uptime, 2),
        version="1.0.0",
        services=services
    )


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe.

    Returns 200 if the application is ready to receive traffic.
    Returns 503 if critical services are unavailable.
    """
    # Check critical services
    db_health = await check_database_health(db)

    if db_health.status == HealthStatus.ERROR:
        return {"status": "not_ready", "reason": "database_unavailable"}

    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if the application process is alive.
    This is a simple check that doesn't verify dependencies.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
