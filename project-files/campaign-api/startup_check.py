#!/usr/bin/env python3
"""
Startup verification script for USB Drop Campaign Manager.

This script runs pre-flight checks before the API starts to ensure
all required services and configurations are ready.

Exit codes:
    0 - All checks passed
    1 - Critical check failed (app should not start)
    2 - Warning (non-critical check failed, app can start with degraded functionality)
"""

import sys
import os
import time
import re
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class StartupChecker:
    """Runs pre-flight checks for the application."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.results = []

    def log(self, level: str, message: str):
        """Log a message with level indicator."""
        icons = {"INFO": "ℹ️ ", "OK": "✅", "WARN": "⚠️ ", "ERROR": "❌"}
        icon = icons.get(level, "  ")
        print(f"{icon} [{level}] {message}")
        self.results.append({"level": level, "message": message})

    def check_env_vars(self) -> bool:
        """Check required environment variables are set."""
        self.log("INFO", "Checking environment variables...")

        required = [
            ("DATABASE_URL", "Database connection string"),
            ("JWT_SECRET_KEY", "JWT secret for authentication"),
        ]

        recommended = [
            ("CANARY_SERVER", "CanaryTokens server URL"),
            ("CANARY_DOMAIN", "CanaryTokens domain"),
            ("OPENAI_API_KEY", "OpenAI API key for content generation"),
        ]

        all_ok = True

        for var, description in required:
            value = os.environ.get(var)
            if not value:
                self.log("ERROR", f"Missing required: {var} ({description})")
                all_ok = False
            else:
                self.log("OK", f"Required variable set: {var}")

        # Check JWT secret strength
        jwt_secret = os.environ.get("JWT_SECRET_KEY", "")
        if jwt_secret and len(jwt_secret) < 32:
            self.log("WARN", "JWT_SECRET_KEY is weak (< 32 characters)")
            self.warnings += 1
        elif jwt_secret == "change-this-secret-key":
            self.log("WARN", "JWT_SECRET_KEY is using default value - INSECURE")
            self.warnings += 1

        # Check admin password
        admin_password = os.environ.get("ADMIN_PASSWORD", "")
        if admin_password and admin_password in ["change-this-password", "admin", "password"]:
            self.log("WARN", "ADMIN_PASSWORD is using a weak/default value")
            self.warnings += 1

        for var, description in recommended:
            value = os.environ.get(var)
            if not value:
                self.log("WARN", f"Optional not set: {var} ({description})")
                self.warnings += 1
            else:
                self.log("OK", f"Optional variable set: {var}")

        return all_ok

    def check_database(self, max_retries: int = 30, retry_delay: float = 2.0) -> bool:
        """Check database connectivity with retries."""
        self.log("INFO", "Checking database connectivity...")

        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            self.log("ERROR", "DATABASE_URL not set")
            return False

        # Mask password in logs
        masked_url = re.sub(r':([^:@]+)@', ':****@', database_url)
        self.log("INFO", f"Connecting to: {masked_url}")

        for attempt in range(1, max_retries + 1):
            try:
                engine = create_engine(database_url, pool_pre_ping=True)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()

                self.log("OK", f"Database connected (attempt {attempt})")

                # Check if tables exist
                with engine.connect() as conn:
                    result = conn.execute(text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    ))
                    table_count = result.fetchone()[0]
                    self.log("INFO", f"Found {table_count} tables in database")

                return True

            except OperationalError as e:
                if attempt < max_retries:
                    self.log("WARN", f"Database not ready (attempt {attempt}/{max_retries}), retrying...")
                    time.sleep(retry_delay)
                else:
                    self.log("ERROR", f"Database connection failed after {max_retries} attempts: {e}")
                    return False

            except Exception as e:
                self.log("ERROR", f"Database error: {e}")
                return False

        return False

    def check_database_schema(self) -> bool:
        """Check database schema and admin user."""
        self.log("INFO", "Checking database schema...")

        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            return False

        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                # Check for users table
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'users')"
                ))
                users_exists = result.fetchone()[0]

                if not users_exists:
                    self.log("WARN", "Users table does not exist (will be created on startup)")
                    return True

                # Check admin user exists
                result = conn.execute(text(
                    "SELECT username, is_active FROM users WHERE username = :username"
                ), {"username": os.environ.get("ADMIN_USERNAME", "admin")})
                admin = result.fetchone()

                if admin:
                    self.log("OK", f"Admin user '{admin[0]}' exists (active: {admin[1]})")

                    # Verify password hash format
                    result = conn.execute(text(
                        "SELECT password_hash FROM users WHERE username = :username"
                    ), {"username": os.environ.get("ADMIN_USERNAME", "admin")})
                    pwd_hash = result.fetchone()[0]

                    if pwd_hash and pwd_hash.startswith("$2"):
                        self.log("OK", "Admin password hash format is valid (bcrypt)")
                    else:
                        self.log("ERROR", "Admin password hash is invalid or corrupted")
                        return False
                else:
                    self.log("INFO", "Admin user does not exist (will be created on startup)")

                return True

        except Exception as e:
            self.log("ERROR", f"Schema check failed: {e}")
            return False

    def check_canarytokens(self, timeout: float = 10.0) -> bool:
        """Check CanaryTokens service connectivity."""
        self.log("INFO", "Checking CanaryTokens service...")

        canary_server = os.environ.get("CANARY_SERVER")
        if not canary_server:
            self.log("WARN", "CANARY_SERVER not configured")
            self.warnings += 1
            return True  # Non-critical

        try:
            # Try to reach the server
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{canary_server}/")
                if response.status_code < 500:
                    self.log("OK", f"CanaryTokens service reachable at {canary_server}")
                    return True
                else:
                    self.log("WARN", f"CanaryTokens returned status {response.status_code}")
                    self.warnings += 1
                    return True  # Non-critical

        except httpx.ConnectError:
            self.log("WARN", f"Cannot connect to CanaryTokens at {canary_server}")
            self.warnings += 1
            return True  # Non-critical

        except Exception as e:
            self.log("WARN", f"CanaryTokens check failed: {e}")
            self.warnings += 1
            return True  # Non-critical

    def check_openai(self) -> bool:
        """Check OpenAI API key format."""
        self.log("INFO", "Checking OpenAI configuration...")

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.log("WARN", "OPENAI_API_KEY not configured (content generation disabled)")
            self.warnings += 1
            return True  # Non-critical

        if not api_key.startswith("sk-"):
            self.log("WARN", "OPENAI_API_KEY has unexpected format (should start with 'sk-')")
            self.warnings += 1
        else:
            self.log("OK", "OpenAI API key format valid")

        return True

    def check_slack(self) -> bool:
        """Check Slack webhook configuration."""
        self.log("INFO", "Checking Slack configuration...")

        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            self.log("INFO", "SLACK_WEBHOOK_URL not configured (notifications disabled)")
            return True

        if "hooks.slack.com" in webhook_url:
            self.log("OK", "Slack webhook URL format valid")
        else:
            self.log("WARN", "SLACK_WEBHOOK_URL may be invalid (expected hooks.slack.com)")
            self.warnings += 1

        return True

    def check_uploads_directory(self) -> bool:
        """Check uploads directory exists and is writable."""
        self.log("INFO", "Checking uploads directory...")

        uploads_dir = "/app/uploads"
        if not os.path.exists(uploads_dir):
            try:
                os.makedirs(uploads_dir, exist_ok=True)
                self.log("OK", f"Created uploads directory: {uploads_dir}")
            except Exception as e:
                self.log("ERROR", f"Cannot create uploads directory: {e}")
                return False

        if os.access(uploads_dir, os.W_OK):
            self.log("OK", f"Uploads directory is writable: {uploads_dir}")
            return True
        else:
            self.log("ERROR", f"Uploads directory is not writable: {uploads_dir}")
            return False

    def run_all_checks(self) -> int:
        """Run all startup checks and return exit code."""
        print("\n" + "=" * 60)
        print("  USB Drop Campaign Manager - Startup Checks")
        print("=" * 60 + "\n")

        critical_checks = [
            ("Environment Variables", self.check_env_vars),
            ("Database Connectivity", self.check_database),
            ("Database Schema", self.check_database_schema),
            ("Uploads Directory", self.check_uploads_directory),
        ]

        optional_checks = [
            ("CanaryTokens Service", self.check_canarytokens),
            ("OpenAI Configuration", self.check_openai),
            ("Slack Configuration", self.check_slack),
        ]

        # Run critical checks
        print("-" * 40)
        print("Critical Checks")
        print("-" * 40)

        critical_failed = False
        for name, check_func in critical_checks:
            try:
                if check_func():
                    self.checks_passed += 1
                else:
                    self.checks_failed += 1
                    critical_failed = True
            except Exception as e:
                self.log("ERROR", f"{name} check crashed: {e}")
                self.checks_failed += 1
                critical_failed = True
            print()

        # Run optional checks
        print("-" * 40)
        print("Optional Checks")
        print("-" * 40)

        for name, check_func in optional_checks:
            try:
                check_func()
                self.checks_passed += 1
            except Exception as e:
                self.log("WARN", f"{name} check failed: {e}")
                self.warnings += 1
            print()

        # Summary
        print("=" * 60)
        print("  Summary")
        print("=" * 60)
        print(f"  ✅ Passed:   {self.checks_passed}")
        print(f"  ❌ Failed:   {self.checks_failed}")
        print(f"  ⚠️  Warnings: {self.warnings}")
        print("=" * 60)

        if critical_failed:
            print("\n❌ STARTUP BLOCKED: Critical checks failed")
            print("   Please fix the errors above before starting the application.\n")
            return 1

        if self.warnings > 0:
            print("\n⚠️  STARTUP OK WITH WARNINGS")
            print("   Some features may be unavailable or degraded.\n")
            return 0  # Continue with warnings

        print("\n✅ ALL CHECKS PASSED - Ready to start\n")
        return 0


def main():
    """Main entry point."""
    checker = StartupChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
