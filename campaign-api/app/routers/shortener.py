"""Short URL router for Shlink integration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import logging

from app.database import get_db
from app.models.short_url import ShortUrl
from app.models.drive import Drive
from app.models.token import Token
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.shlink_client import ShlinkClient, ShlinkError, SlugExistsError
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class ShortUrlResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID
    token_id: uuid.UUID
    base_slug: str
    suffix_mode: str
    generated_suffix: str
    full_slug: str
    shlink_short_code: str
    shlink_domain: str
    canary_url: str
    short_url: str

    class Config:
        from_attributes = True


class CreateShortUrlRequest(BaseModel):
    canary_url: str
    base_slug: str
    suffix_mode: str = "random"  # random, sequential, drive_code, custom
    suffix_length: int = 4
    custom_suffix: Optional[str] = None
    domain: Optional[str] = None


class ShortUrlStats(BaseModel):
    short_code: str
    total_visits: int
    visits: list


@router.post("/drives/{drive_id}/tokens/{token_id}", response_model=ShortUrlResponse)
async def create_short_url_for_token(
    drive_id: uuid.UUID,
    token_id: uuid.UUID,
    request: CreateShortUrlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a short URL for a specific token."""
    # Verify drive and token exist
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    token = db.query(Token).filter(Token.id == token_id, Token.drive_id == drive_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Check if short URL already exists for this token
    existing = db.query(ShortUrl).filter(ShortUrl.token_id == token_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Short URL already exists for this token")

    # Create short URL via Shlink
    client = ShlinkClient()
    try:
        result = await client.create_drive_short_url(
            canary_url=request.canary_url,
            base_slug=request.base_slug,
            suffix_mode=request.suffix_mode,
            drive_code=drive.unique_code,
            drive_id=str(drive_id),
            token_id=str(token_id),
            suffix_length=request.suffix_length,
            custom_suffix=request.custom_suffix,
            domain=request.domain,
        )
    except SlugExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShlinkError as e:
        logger.error(f"Shlink error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create short URL")

    # Save to database
    short_url = ShortUrl(
        drive_id=drive_id,
        token_id=token_id,
        base_slug=result["base_slug"],
        suffix_mode=result["suffix_mode"],
        generated_suffix=result["generated_suffix"],
        full_slug=result["full_slug"],
        shlink_short_code=result["shortCode"],
        shlink_domain=result.get("domain", settings.shlink_default_domain),
        canary_url=request.canary_url,
        short_url=result["shortUrl"],
    )
    db.add(short_url)
    db.commit()
    db.refresh(short_url)

    return short_url


@router.get("/drives/{drive_id}", response_model=List[ShortUrlResponse])
async def get_drive_short_urls(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all short URLs for a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    short_urls = db.query(ShortUrl).filter(ShortUrl.drive_id == drive_id).all()
    return short_urls


@router.get("/{short_url_id}", response_model=ShortUrlResponse)
async def get_short_url(
    short_url_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific short URL."""
    short_url = db.query(ShortUrl).filter(ShortUrl.id == short_url_id).first()
    if not short_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return short_url


@router.get("/{short_url_id}/stats", response_model=ShortUrlStats)
async def get_short_url_stats(
    short_url_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get visit statistics for a short URL."""
    short_url = db.query(ShortUrl).filter(ShortUrl.id == short_url_id).first()
    if not short_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    client = ShlinkClient()
    try:
        result = await client.get_visits(
            short_url.shlink_short_code,
            short_url.shlink_domain
        )
        return {
            "short_code": short_url.shlink_short_code,
            "total_visits": result.get("visits", {}).get("pagination", {}).get("totalItems", 0),
            "visits": result.get("visits", {}).get("data", []),
        }
    except ShlinkError as e:
        logger.error(f"Shlink error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.delete("/{short_url_id}")
async def delete_short_url(
    short_url_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a short URL."""
    short_url = db.query(ShortUrl).filter(ShortUrl.id == short_url_id).first()
    if not short_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Delete from Shlink
    client = ShlinkClient()
    try:
        await client.delete_short_url(
            short_url.shlink_short_code,
            short_url.shlink_domain
        )
    except ShlinkError:
        pass  # Continue even if remote delete fails

    db.delete(short_url)
    db.commit()
    return {"message": "Short URL deleted"}


@router.post("/bulk/drives/{drive_id}")
async def create_bulk_short_urls(
    drive_id: uuid.UUID,
    base_slug: str,
    suffix_mode: str = "random",
    suffix_length: int = 4,
    domain: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create short URLs for all tokens on a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    tokens = db.query(Token).filter(Token.drive_id == drive_id).all()
    if not tokens:
        raise HTTPException(status_code=400, detail="Drive has no tokens")

    client = ShlinkClient()
    created = []
    errors = []

    for token in tokens:
        # Skip if short URL already exists
        existing = db.query(ShortUrl).filter(ShortUrl.token_id == token.id).first()
        if existing:
            continue

        # Get the canary URL from the token
        canary_url = token.url
        if not canary_url:
            errors.append({"token_id": str(token.id), "error": "Token has no URL"})
            continue

        try:
            result = await client.create_drive_short_url(
                canary_url=canary_url,
                base_slug=base_slug,
                suffix_mode=suffix_mode,
                drive_code=drive.unique_code,
                drive_id=str(drive_id),
                token_id=str(token.id),
                suffix_length=suffix_length,
                domain=domain,
            )

            short_url = ShortUrl(
                drive_id=drive_id,
                token_id=token.id,
                base_slug=result["base_slug"],
                suffix_mode=result["suffix_mode"],
                generated_suffix=result["generated_suffix"],
                full_slug=result["full_slug"],
                shlink_short_code=result["shortCode"],
                shlink_domain=result.get("domain", settings.shlink_default_domain),
                canary_url=canary_url,
                short_url=result["shortUrl"],
            )
            db.add(short_url)
            created.append({"token_id": str(token.id), "short_url": result["shortUrl"]})

        except ShlinkError as e:
            errors.append({"token_id": str(token.id), "error": str(e)})

    db.commit()

    return {
        "created": len(created),
        "errors": len(errors),
        "details": {
            "created": created,
            "errors": errors,
        }
    }
