"""Database helper utilities."""

from typing import TypeVar, Type, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

T = TypeVar("T")


def get_or_404(
    db: Session,
    model: Type[T],
    id: Any,
    detail: Optional[str] = None
) -> T:
    """
    Get an entity by ID or raise 404 if not found.

    Args:
        db: SQLAlchemy session
        model: SQLAlchemy model class
        id: Primary key value (usually UUID)
        detail: Custom error message (optional)

    Returns:
        The found entity

    Raises:
        HTTPException: 404 if entity not found

    Example:
        campaign = get_or_404(db, Campaign, campaign_id)
        drive = get_or_404(db, Drive, drive_id, "Drive not found")
    """
    entity = db.query(model).filter(model.id == id).first()
    if not entity:
        model_name = model.__name__
        raise HTTPException(
            status_code=404,
            detail=detail or f"{model_name} not found"
        )
    return entity


def get_by_field_or_404(
    db: Session,
    model: Type[T],
    field_name: str,
    value: Any,
    detail: Optional[str] = None
) -> T:
    """
    Get an entity by any field or raise 404 if not found.

    Args:
        db: SQLAlchemy session
        model: SQLAlchemy model class
        field_name: Name of the field to filter by
        value: Value to match
        detail: Custom error message (optional)

    Returns:
        The found entity

    Raises:
        HTTPException: 404 if entity not found

    Example:
        drive = get_by_field_or_404(db, Drive, "unique_code", "USB-A1B2C3")
    """
    field = getattr(model, field_name)
    entity = db.query(model).filter(field == value).first()
    if not entity:
        model_name = model.__name__
        raise HTTPException(
            status_code=404,
            detail=detail or f"{model_name} not found"
        )
    return entity
