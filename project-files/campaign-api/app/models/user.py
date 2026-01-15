"""User and API Key models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, PyEnum):
    """User roles for access control."""
    ADMIN = "admin"      # Full access: user management, all operations
    OPERATOR = "operator"  # Can manage campaigns, drives, profiles
    VIEWER = "viewer"    # Read-only access


class User(Base):
    """User account for authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_admin = Column(Boolean, default=False)  # Kept for backward compatibility
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    @property
    def has_admin_access(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN or self.is_admin

    @property
    def has_write_access(self) -> bool:
        """Check if user can create/modify resources."""
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR) or self.is_admin

    @property
    def effective_role(self) -> UserRole:
        """Get effective role (handles legacy is_admin)."""
        if self.is_admin and self.role == UserRole.VIEWER:
            return UserRole.ADMIN
        return self.role


class APIKey(Base):
    """API keys for CLI and programmatic access."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")
