"""Authentication router."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
import uuid
import re

from app.database import get_db
from app.models.user import User, APIKey, UserRole
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    generate_api_key,
    verify_api_key,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Password validation
def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
    return password


# Pydantic models
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

    @field_validator('role', mode='before')
    @classmethod
    def convert_role(cls, v):
        if hasattr(v, 'value'):
            return v.value
        return str(v).lower() if v else 'viewer'


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=12)
    role: UserRole = UserRole.VIEWER

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)

    @field_validator('username')
    @classmethod
    def username_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=12)

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)


class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key: Optional[str] = None  # Only returned on creation
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    refresh_token: str


# Dependency to get current user
async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token or X-API-Key header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Prefer X-API-Key header if present
    if x_api_key and x_api_key.startswith("usbdrop_"):
        user = verify_api_key(db, x_api_key)
        if user:
            return user
        raise credentials_exception

    # Fall back to OAuth2 bearer token
    if not token:
        raise credentials_exception

    # Check if bearer token is actually an API key (legacy support)
    if token.startswith("usbdrop_"):
        user = verify_api_key(db, token)
        if user:
            return user
        raise credentials_exception

    # Decode JWT
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    if not current_user.has_admin_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_current_operator(current_user: User = Depends(get_current_user)) -> User:
    """Require at least operator privileges (admin or operator can access)."""
    if not current_user.has_write_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator privileges required"
        )
    return current_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user."""
    key, key_hash, key_prefix = generate_api_key()

    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=key,  # Only returned on creation
        created_at=api_key.created_at,
        last_used=api_key.last_used,
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List API keys for current user."""
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    return keys


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    db.commit()

    return {"message": "API key deleted"}


# ============================================================================
# User Management Endpoints (Admin only)
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with hashed password
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        is_admin=(user_data.role == UserRole.ADMIN),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if user.id == current_user.id and user_data.role and user_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Prevent admin from deactivating themselves
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    # Check email uniqueness if changing
    if user_data.email and user_data.email != user.email:
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email

    if user_data.role is not None:
        user.role = user_data.role
        user.is_admin = (user_data.role == UserRole.ADMIN)

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only). Performs soft delete by deactivating."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Soft delete - deactivate instead of removing
    user.is_active = False
    db.commit()

    return {"message": f"User {user.username} has been deactivated"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: uuid.UUID,
    password_data: AdminPasswordReset,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": f"Password reset for user {user.username}"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change own password (any authenticated user)."""
    from app.services.auth_service import verify_password

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Ensure new password is different
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.get("/roles")
async def list_roles(current_user: User = Depends(get_current_admin)):
    """List available user roles (admin only)."""
    return {
        "roles": [
            {
                "value": UserRole.ADMIN.value,
                "label": "Admin",
                "description": "Full access: user management, all operations"
            },
            {
                "value": UserRole.OPERATOR.value,
                "label": "Operator",
                "description": "Can manage campaigns, drives, profiles"
            },
            {
                "value": UserRole.VIEWER.value,
                "label": "Viewer",
                "description": "Read-only access to dashboards and reports"
            }
        ]
    }
