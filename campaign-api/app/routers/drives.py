"""Drives router - USB drive management."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import io
import zipfile
import os
import aiofiles

from app.database import get_db
from app.models.drive import Drive, DriveStatus
from app.models.campaign import Campaign
from app.models.profile import Profile
from app.models.deployment import Deployment
from app.models.token import Token
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.canary_client import CanaryTokensClient
from app.services.usb_builder import USBBuilder
from app.services.exif_service import extract_photo_metadata

router = APIRouter()


# Pydantic models
class DriveCreate(BaseModel):
    campaign_id: uuid.UUID
    profile_id: Optional[uuid.UUID] = None
    label: Optional[str] = None
    drive_brand: Optional[str] = None
    drive_capacity: Optional[str] = None
    notes: Optional[str] = None
    url_config: Optional[dict] = None


class DriveUpdate(BaseModel):
    profile_id: Optional[uuid.UUID] = None
    label: Optional[str] = None
    drive_brand: Optional[str] = None
    drive_capacity: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[DriveStatus] = None
    url_config: Optional[dict] = None


class DeploymentCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    location_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    deployed_by: Optional[str] = None
    deployment_notes: Optional[str] = None


class DriveResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    profile_id: Optional[uuid.UUID]
    unique_code: str
    status: DriveStatus
    label: Optional[str]
    drive_brand: Optional[str]
    drive_capacity: Optional[str]
    files_manifest: dict
    url_config: Optional[dict]
    notes: Optional[str]
    created_at: datetime
    prepared_at: Optional[datetime]
    deployed_at: Optional[datetime]
    triggered_at: Optional[datetime]
    trigger_count: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    id: uuid.UUID
    canary_token_id: str
    token_type: str
    filename: Optional[str]
    memo: Optional[str]
    url: Optional[str]
    created_at: datetime
    is_triggered: bool
    trigger_count: int

    class Config:
        from_attributes = True


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    location_description: Optional[str]
    location_type: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    photo_url: Optional[str]
    deployed_by: Optional[str]
    deployment_notes: Optional[str]
    deployed_at: datetime
    photo_taken_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("", response_model=List[DriveResponse])
async def list_drives(
    campaign_id: Optional[uuid.UUID] = None,
    status: Optional[DriveStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all drives."""
    query = db.query(Drive)
    if campaign_id:
        query = query.filter(Drive.campaign_id == campaign_id)
    if status:
        query = query.filter(Drive.status == status)
    query = query.order_by(Drive.created_at.desc())
    drives = query.offset(skip).limit(limit).all()
    return drives


@router.post("", response_model=DriveResponse)
async def create_drive(
    drive_data: DriveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new drive record."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == drive_data.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify profile exists if provided
    if drive_data.profile_id:
        profile = db.query(Profile).filter(Profile.id == drive_data.profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    drive = Drive(**drive_data.model_dump())
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive


@router.get("/by-code/{code}", response_model=DriveResponse)
async def get_drive_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drive by unique code."""
    drive = db.query(Drive).filter(Drive.unique_code == code).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drive by ID."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


@router.put("/{drive_id}", response_model=DriveResponse)
async def update_drive(
    drive_id: uuid.UUID,
    drive_data: DriveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    # Validate profile_id if being updated
    if drive_data.profile_id is not None:
        if drive.status != DriveStatus.CREATED:
            raise HTTPException(status_code=400, detail="Cannot change profile after drive is prepared")
        profile = db.query(Profile).filter(Profile.id == drive_data.profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    update_data = drive_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(drive, key, value)

    db.commit()
    db.refresh(drive)
    return drive


@router.delete("/{drive_id}")
async def delete_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a drive and all associated tokens."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    drive_code = drive.unique_code
    tokens_deleted = 0
    tokens_failed = 0

    # Delete tokens from CanaryTokens API
    canary_client = CanaryTokensClient()
    for token in drive.tokens or []:
        if token.canary_token_id and token.auth_token:
            try:
                await canary_client.delete_token(token.canary_token_id, token.auth_token)
                tokens_deleted += 1
            except Exception as e:
                tokens_failed += 1

    # Delete drive (cascades to tokens and deployment)
    db.delete(drive)
    db.commit()

    return {
        "message": f"Drive '{drive_code}' deleted",
        "tokens_deleted": tokens_deleted,
        "tokens_failed": tokens_failed
    }


@router.post("/{drive_id}/prepare", response_model=DriveResponse)
async def prepare_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prepare a drive - create tokens based on profile."""
    from sqlalchemy.exc import OperationalError

    # Use with_for_update() to lock the row and prevent concurrent prepare requests
    try:
        drive = db.query(Drive).filter(Drive.id == drive_id).with_for_update(nowait=True).first()
    except OperationalError:
        raise HTTPException(status_code=409, detail="Drive is currently being prepared by another request")
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if not drive.profile_id:
        raise HTTPException(status_code=400, detail="Drive has no profile assigned")

    if drive.status != DriveStatus.CREATED:
        raise HTTPException(status_code=400, detail="Drive is already prepared or being prepared")

    profile = db.query(Profile).filter(Profile.id == drive.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create tokens using CanaryTokens API
    try:
        builder = USBBuilder(db)
        files_manifest = await builder.prepare_drive(drive, profile)

        drive.files_manifest = files_manifest
        drive.status = DriveStatus.PREPARED
        drive.prepared_at = datetime.utcnow()
        db.commit()
        db.refresh(drive)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to prepare drive: {str(e)}")

    return drive


@router.get("/{drive_id}/download")
async def download_drive_zip(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a ZIP file containing all drive files."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status == DriveStatus.CREATED:
        raise HTTPException(status_code=400, detail="Drive not prepared yet")

    # Build ZIP file in memory
    try:
        builder = USBBuilder(db)
        zip_buffer = await builder.create_zip(drive)

        return StreamingResponse(
            io.BytesIO(zip_buffer),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={drive.unique_code}.zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")


@router.post("/{drive_id}/deploy", response_model=DeploymentResponse)
async def deploy_drive(
    drive_id: uuid.UUID,
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record deployment of a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status not in [DriveStatus.PREPARED, DriveStatus.DEPLOYED, DriveStatus.TRIGGERED]:
        raise HTTPException(status_code=400, detail="Drive must be prepared before deployment")

    # Check if already deployed
    existing = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()
    if existing:
        # Update existing deployment
        for key, value in deployment_data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        deployment = existing
    else:
        # Create new deployment
        deployment = Deployment(
            drive_id=drive_id,
            **deployment_data.model_dump()
        )
        db.add(deployment)

    # Update drive status (don't downgrade from TRIGGERED)
    if drive.status == DriveStatus.PREPARED:
        drive.status = DriveStatus.DEPLOYED
        drive.deployed_at = datetime.utcnow()

    db.commit()
    db.refresh(deployment)
    return deployment


@router.post("/{drive_id}/deploy-with-photo", response_model=DeploymentResponse)
async def deploy_drive_with_photo(
    drive_id: uuid.UUID,
    photo: UploadFile = File(..., description="Deployment photo with GPS metadata"),
    location_name: Optional[str] = Form(None),
    location_description: Optional[str] = Form(None),
    location_type: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    deployed_by: Optional[str] = Form(None),
    deployment_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record deployment of a drive with a photo.
    GPS coordinates and timestamp are automatically extracted from photo EXIF data.
    """
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status not in [DriveStatus.PREPARED, DriveStatus.DEPLOYED, DriveStatus.TRIGGERED]:
        raise HTTPException(status_code=400, detail="Drive must be prepared before deployment")

    # Validate file type
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read photo data
    photo_data = await photo.read()

    # Extract EXIF metadata
    metadata = extract_photo_metadata(photo_data)

    # Save photo to uploads directory
    upload_dir = "/app/uploads/deployments"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    file_ext = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
    photo_filename = f"{drive_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    photo_path = os.path.join(upload_dir, photo_filename)

    async with aiofiles.open(photo_path, 'wb') as f:
        await f.write(photo_data)

    photo_url = f"/uploads/deployments/{photo_filename}"

    # Check if already deployed
    existing = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()

    deployment_data = {
        "latitude": metadata["latitude"],
        "longitude": metadata["longitude"],
        "location_name": location_name,
        "location_description": location_description,
        "location_type": location_type,
        "address": address,
        "city": city,
        "state": state,
        "country": country,
        "photo_url": photo_url,
        "deployed_by": deployed_by or current_user.username,
        "deployment_notes": deployment_notes,
        "photo_taken_at": metadata["datetime"],
    }

    if existing:
        # Update existing deployment
        for key, value in deployment_data.items():
            if value is not None:
                setattr(existing, key, value)
        existing.deployed_at = datetime.utcnow()
        deployment = existing
    else:
        # Create new deployment
        deployment = Deployment(
            drive_id=drive_id,
            deployed_at=datetime.utcnow(),
            **{k: v for k, v in deployment_data.items() if v is not None}
        )
        db.add(deployment)

    # Update drive status (don't downgrade from TRIGGERED)
    if drive.status == DriveStatus.PREPARED:
        drive.status = DriveStatus.DEPLOYED
        drive.deployed_at = datetime.utcnow()

    db.commit()
    db.refresh(deployment)

    return deployment


@router.get("/{drive_id}/tokens", response_model=List[TokenResponse])
async def get_drive_tokens(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tokens for a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    return drive.tokens or []


@router.get("/{drive_id}/deployment", response_model=DeploymentResponse)
async def get_drive_deployment(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get deployment info for a drive."""
    deployment = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return deployment


@router.put("/{drive_id}/deployment", response_model=DeploymentResponse)
async def update_drive_deployment(
    drive_id: uuid.UUID,
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update deployment details for a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status not in [DriveStatus.DEPLOYED, DriveStatus.TRIGGERED, DriveStatus.RECOVERED]:
        raise HTTPException(status_code=400, detail="Drive must be deployed to update deployment details")

    deployment = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    # Update deployment fields
    for key, value in deployment_data.model_dump(exclude_unset=True).items():
        setattr(deployment, key, value)

    db.commit()
    db.refresh(deployment)
    return deployment
