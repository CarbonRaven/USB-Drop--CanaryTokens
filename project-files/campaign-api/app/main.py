"""USB Drop Campaign Manager - FastAPI Application."""

import os
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import httpx
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, campaigns, profiles, drives, tokens, webhooks, alerts, generate, reports, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class StartupVerificationError(Exception):
    """Raised when a critical startup check fails."""
    pass


async def verify_database_connection():
    """Verify database connectivity during startup."""
    logger.info("Verifying database connection...")
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection verified")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise StartupVerificationError(f"Database connection failed: {e}")


async def verify_database_schema():
    """Verify critical database tables exist."""
    logger.info("Verifying database schema...")
    try:
        db = SessionLocal()
        result = db.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        ))
        tables = [row[0] for row in result.fetchall()]
        db.close()

        # After initial startup, we expect these tables
        expected = {"users", "campaigns", "drives", "tokens", "triggers"}
        found = set(tables) & expected
        logger.info(f"Found tables: {', '.join(found) if found else 'none'}")
        return True
    except Exception as e:
        logger.warning(f"Schema verification warning: {e}")
        return True  # Non-critical, tables will be created


async def verify_admin_user():
    """Verify admin user exists and has valid configuration."""
    logger.info("Verifying admin user...")
    try:
        db = SessionLocal()
        result = db.execute(text(
            "SELECT username, password_hash, is_active FROM users WHERE username = :username"
        ), {"username": settings.admin_username})
        admin = result.fetchone()
        db.close()

        if admin:
            username, pwd_hash, is_active = admin
            if not pwd_hash or not pwd_hash.startswith("$2"):
                logger.error("Admin user has invalid password hash format!")
                raise StartupVerificationError(
                    "Admin password hash is invalid. Please reset the admin password."
                )
            if not is_active:
                logger.warning("Admin user is inactive")
            logger.info(f"Admin user '{username}' verified")
        else:
            logger.info("Admin user will be created")
        return True
    except StartupVerificationError:
        raise
    except Exception as e:
        logger.warning(f"Admin verification skipped: {e}")
        return True  # Table may not exist yet


async def verify_canarytokens_service():
    """Verify CanaryTokens service is reachable (non-blocking)."""
    if not settings.canary_server:
        logger.warning("CanaryTokens server not configured")
        return True

    logger.info(f"Checking CanaryTokens service at {settings.canary_server}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.canary_server}/")
            if response.status_code < 500:
                logger.info("CanaryTokens service is reachable")
            else:
                logger.warning(f"CanaryTokens returned status {response.status_code}")
        return True
    except Exception as e:
        logger.warning(f"CanaryTokens service check failed: {e}")
        return True  # Non-critical


def verify_configuration():
    """Verify critical configuration on startup."""
    logger.info("Verifying configuration...")
    warnings = []

    # Check JWT secret
    if settings.jwt_secret_key == "change-this-secret-key":
        warnings.append("JWT_SECRET_KEY is using default value - INSECURE!")
    elif len(settings.jwt_secret_key) < 32:
        warnings.append("JWT_SECRET_KEY is weak (< 32 characters)")

    # Check admin password
    if settings.admin_password in ["change-this-password", "admin", "password", ""]:
        warnings.append("ADMIN_PASSWORD is using weak/default value")

    # Check OpenAI key format
    if settings.openai_api_key and not settings.openai_api_key.startswith("sk-"):
        warnings.append("OPENAI_API_KEY has unexpected format")

    for warning in warnings:
        logger.warning(f"Configuration: {warning}")

    logger.info("Configuration verification complete")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with enhanced startup verification."""
    # Startup
    logger.info("=" * 60)
    logger.info("Starting USB Drop Campaign Manager...")
    logger.info("=" * 60)

    # Run startup verifications
    try:
        # Critical checks (will raise on failure)
        verify_configuration()
        await verify_database_connection()

        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

        # Verify schema and admin
        await verify_database_schema()

        # Create initial admin user if not exists
        from app.services.auth_service import create_initial_admin
        create_initial_admin()

        # Verify admin user configuration
        await verify_admin_user()

        # Non-critical service checks
        await verify_canarytokens_service()

        logger.info("=" * 60)
        logger.info("Startup verification complete - Application ready")
        logger.info("=" * 60)

    except StartupVerificationError as e:
        logger.error("=" * 60)
        logger.error(f"STARTUP FAILED: {e}")
        logger.error("=" * 60)
        raise

    yield

    # Shutdown
    logger.info("Shutting down USB Drop Campaign Manager...")


# Create FastAPI app
app = FastAPI(
    title="USB Drop Campaign Manager",
    description="API for managing USB drop penetration testing campaigns with CanaryTokens",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"https://app.{settings.canary_domain}",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(drives.router, prefix="/api/drives", tags=["Drives"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Tokens"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(generate.router, prefix="/api/generate", tags=["Content Generation"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "USB Drop Campaign Manager",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health/detailed",
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint (legacy)."""
    return {"status": "healthy"}
