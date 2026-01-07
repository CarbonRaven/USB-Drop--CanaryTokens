"""Targets router - Organization profiles for targeted campaigns."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.target import Target, INDUSTRIES, COMPANY_SIZES, DEPARTMENTS, REGIONS
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.ai_scenario import AIScenarioService

router = APIRouter()


# Pydantic models
class TargetCreate(BaseModel):
    name: str
    company_name: str
    industry: str = "other"
    company_size: str = "mid_market"
    target_department: Optional[str] = None
    geographic_region: Optional[str] = "us_east"
    known_technologies: List[str] = []
    email_domain: Optional[str] = None
    osint_notes: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    target_department: Optional[str] = None
    geographic_region: Optional[str] = None
    known_technologies: Optional[List[str]] = None
    email_domain: Optional[str] = None
    osint_notes: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None


class TargetResponse(BaseModel):
    id: uuid.UUID
    name: str
    company_name: str
    industry: str
    company_size: str
    target_department: Optional[str]
    geographic_region: Optional[str]
    known_technologies: List[str]
    email_domain: Optional[str]
    osint_notes: Optional[str]
    website: Optional[str]
    linkedin_url: Optional[str]
    recommended_scenario: Optional[str]
    scenario_reasoning: Optional[str]
    suggested_labels: List[str]
    created_at: datetime
    updated_at: datetime
    campaign_count: int = 0

    class Config:
        from_attributes = True


class ScenarioRecommendation(BaseModel):
    recommended_profile: str
    confidence: str  # high, medium, low
    reasoning: str
    alternative_profiles: List[str]
    suggested_labels: List[str]
    suggested_filenames: List[str]
    risk_factors: List[str]
    tips: List[str]


class OptionsResponse(BaseModel):
    industries: List[str]
    company_sizes: List[str]
    departments: List[str]
    regions: List[str]


# Routes
@router.get("/options", response_model=OptionsResponse)
async def get_options(
    current_user: User = Depends(get_current_user),
):
    """Get available options for target fields."""
    return OptionsResponse(
        industries=INDUSTRIES,
        company_sizes=COMPANY_SIZES,
        departments=DEPARTMENTS,
        regions=REGIONS,
    )


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    industry: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all targets."""
    query = db.query(Target)
    if industry:
        query = query.filter(Target.industry == industry)
    targets = query.order_by(Target.updated_at.desc()).all()

    # Add campaign count to response
    results = []
    for target in targets:
        target_dict = {
            "id": target.id,
            "name": target.name,
            "company_name": target.company_name,
            "industry": target.industry,
            "company_size": target.company_size,
            "target_department": target.target_department,
            "geographic_region": target.geographic_region,
            "known_technologies": target.known_technologies or [],
            "email_domain": target.email_domain,
            "osint_notes": target.osint_notes,
            "website": target.website,
            "linkedin_url": target.linkedin_url,
            "recommended_scenario": target.recommended_scenario,
            "scenario_reasoning": target.scenario_reasoning,
            "suggested_labels": target.suggested_labels or [],
            "created_at": target.created_at,
            "updated_at": target.updated_at,
            "campaign_count": len(target.campaigns) if target.campaigns else 0,
        }
        results.append(target_dict)

    return results


@router.post("", response_model=TargetResponse)
async def create_target(
    target_data: TargetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new target."""
    target = Target(**target_data.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)

    return {
        **target.__dict__,
        "known_technologies": target.known_technologies or [],
        "suggested_labels": target.suggested_labels or [],
        "campaign_count": 0,
    }


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get target by ID."""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return {
        **target.__dict__,
        "known_technologies": target.known_technologies or [],
        "suggested_labels": target.suggested_labels or [],
        "campaign_count": len(target.campaigns) if target.campaigns else 0,
    }


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: uuid.UUID,
    target_data: TargetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a target."""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    update_data = target_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(target, key, value)

    # Clear cached recommendations if key fields changed
    if any(k in update_data for k in ["industry", "company_size", "target_department", "known_technologies"]):
        target.recommended_scenario = None
        target.scenario_reasoning = None
        target.suggested_labels = []

    db.commit()
    db.refresh(target)

    return {
        **target.__dict__,
        "known_technologies": target.known_technologies or [],
        "suggested_labels": target.suggested_labels or [],
        "campaign_count": len(target.campaigns) if target.campaigns else 0,
    }


@router.delete("/{target_id}")
async def delete_target(
    target_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a target."""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Check if target has campaigns
    if target.campaigns and len(target.campaigns) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete target with {len(target.campaigns)} associated campaigns"
        )

    db.delete(target)
    db.commit()
    return {"message": "Target deleted"}


@router.post("/{target_id}/recommend-scenario", response_model=ScenarioRecommendation)
async def recommend_scenario(
    target_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get AI-powered scenario recommendation for a target."""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Call AI service
    ai_service = AIScenarioService()
    recommendation = await ai_service.recommend_scenario(target)

    # Cache the recommendation
    target.recommended_scenario = recommendation["recommended_profile"]
    target.scenario_reasoning = recommendation["reasoning"]
    target.suggested_labels = recommendation["suggested_labels"]
    db.commit()

    return recommendation
