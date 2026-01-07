"""Campaigns router."""

from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    target_drive_count: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    landing_page_config: Optional[dict] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    target_drive_count: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[CampaignStatus] = None
    notes: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    landing_page_config: Optional[dict] = None


class TargetSummary(BaseModel):
    id: uuid.UUID
    name: str
    company_name: str
    industry: str
    recommended_scenario: Optional[str]

    class Config:
        from_attributes = True


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    client_name: Optional[str]
    description: Optional[str]
    target_drive_count: int
    start_date: Optional[date]
    end_date: Optional[date]
    status: CampaignStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    drive_count: int
    deployed_count: int
    triggered_count: int
    target_id: Optional[uuid.UUID]
    target: Optional[TargetSummary]
    landing_page_config: Optional[dict] = None

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    total_drives: int
    created: int
    prepared: int
    deployed: int
    triggered: int
    recovered: int
    total_triggers: int
    unique_ips: int


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all campaigns."""
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    query = query.order_by(Campaign.created_at.desc())
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign."""
    from app.models.target import Target

    # Validate target_id if provided
    if campaign_data.target_id:
        target = db.query(Target).filter(Target.id == campaign_data.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

    campaign = Campaign(**campaign_data.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


# Available landing page themes for configuration
# This route MUST be before /{campaign_id} to avoid path conflicts
LANDING_PAGE_THEMES = [
    {"id": "corporate", "name": "Corporate Portal", "description": "Professional secure document portal"},
    {"id": "login", "name": "Login Page", "description": "Corporate login form (Gmail-style)"},
    {"id": "maintenance", "name": "Maintenance", "description": "System maintenance notice"},
    {"id": "helpdesk", "name": "IT Helpdesk", "description": "IT support portal with ticket system"},
    {"id": "hrportal", "name": "HR Portal", "description": "HR/Payroll portal"},
    {"id": "fileshare", "name": "File Share", "description": "File sharing/download interface"},
    {"id": "training", "name": "Training Portal", "description": "Learning management system"},
    {"id": "banking", "name": "Banking Portal", "description": "Banking verification page"},
    {"id": "document", "name": "Document Viewer", "description": "Document viewer page"},
    {"id": "survey", "name": "Survey", "description": "Survey/feedback form"},
    {"id": "onlyfans", "name": "Premium Content", "description": "Premium/exclusive content access"},
]


@router.get("/landing-pages/themes")
async def list_landing_page_themes(
    current_user: User = Depends(get_current_user),
):
    """List available landing page themes."""
    return {"themes": LANDING_PAGE_THEMES}


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign by ID."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = campaign_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return campaign


class DeletePreview(BaseModel):
    campaign_name: str
    drive_count: int
    deployed_count: int
    triggered_count: int
    token_count: int
    drives: List[dict]


@router.get("/{campaign_id}/delete-preview", response_model=DeletePreview)
async def preview_campaign_deletion(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview what will be deleted when deleting a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []
    token_count = sum(len(d.tokens) if d.tokens else 0 for d in drives)

    drive_summaries = [
        {
            "id": str(d.id),
            "unique_code": d.unique_code,
            "status": d.status.value,
            "label": d.label,
            "token_count": len(d.tokens) if d.tokens else 0
        }
        for d in drives
    ]

    return DeletePreview(
        campaign_name=campaign.name,
        drive_count=len(drives),
        deployed_count=campaign.deployed_count,
        triggered_count=campaign.triggered_count,
        token_count=token_count,
        drives=drive_summaries
    )


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign and all associated drives. Requires confirm=true."""
    from app.services.canary_client import CanaryTokensClient
    import logging

    logger = logging.getLogger(__name__)

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deletion requires confirmation. Use ?confirm=true to proceed."
        )

    drive_count = len(campaign.drives) if campaign.drives else 0
    campaign_name = campaign.name

    # Delete CanaryTokens from the server before removing database records
    tokens_deleted = 0
    tokens_failed = 0
    canary_client = CanaryTokensClient()

    for drive in campaign.drives or []:
        for token in drive.tokens or []:
            if token.canary_token_id and token.auth_token:
                try:
                    await canary_client.delete_token(token.canary_token_id, token.auth_token)
                    tokens_deleted += 1
                    logger.info(f"Deleted CanaryToken: {token.canary_token_id}")
                except Exception as e:
                    tokens_failed += 1
                    logger.warning(f"Failed to delete CanaryToken {token.canary_token_id}: {e}")

    # Delete campaign and cascade to drives/tokens in database
    db.delete(campaign)
    db.commit()

    return {
        "message": f"Campaign '{campaign_name}' deleted",
        "drives_deleted": drive_count,
        "tokens_deleted": tokens_deleted,
        "tokens_failed": tokens_failed
    }


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign statistics."""
    from app.models.drive import Drive, DriveStatus
    from app.models.trigger import Trigger

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []

    # Count by status
    status_counts = {
        "created": 0,
        "prepared": 0,
        "deployed": 0,
        "triggered": 0,
        "recovered": 0,
    }
    for drive in drives:
        status_counts[drive.status.value] += 1

    # Get all triggers for this campaign
    drive_ids = [d.id for d in drives]
    triggers = []
    if drive_ids:
        from app.models.token import Token
        triggers = db.query(Trigger).join(Token).filter(Token.drive_id.in_(drive_ids)).all()

    unique_ips = set()
    for trigger in triggers:
        if trigger.source_ip:
            unique_ips.add(str(trigger.source_ip))

    return CampaignStats(
        total_drives=len(drives),
        created=status_counts["created"],
        prepared=status_counts["prepared"],
        deployed=status_counts["deployed"],
        triggered=status_counts["triggered"],
        recovered=status_counts["recovered"],
        total_triggers=len(triggers),
        unique_ips=len(unique_ips),
    )
