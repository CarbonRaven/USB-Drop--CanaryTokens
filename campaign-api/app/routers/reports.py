"""Reports router."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from collections import defaultdict
import uuid
import io
import csv
import statistics

from app.database import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.drive import Drive, DriveStatus
from app.models.profile import Profile
from app.models.token import Token
from app.models.trigger import Trigger
from app.models.deployment import Deployment
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# =============================================================================
# Pydantic Models for New Reports
# =============================================================================

class ExecutiveSummary(BaseModel):
    """Executive summary report for stakeholders."""
    campaign_id: uuid.UUID
    campaign_name: str
    client_name: Optional[str]

    # Key metrics
    total_drives: int
    drives_deployed: int
    drives_triggered: int
    plug_in_rate: float  # triggered / deployed * 100

    # Time metrics
    avg_time_to_trigger_minutes: Optional[float]
    min_time_to_trigger_minutes: Optional[float]
    max_time_to_trigger_minutes: Optional[float]

    # Risk assessment
    risk_level: str  # Critical, High, Medium, Low
    risk_score: int  # 0-100

    # Key findings
    key_findings: List[str]

    # Dates
    campaign_start: Optional[str]
    campaign_end: Optional[str]
    first_trigger: Optional[datetime]
    last_trigger: Optional[datetime]

    # Additional context
    total_triggers: int
    unique_ips: int
    most_effective_profile: Optional[str]
    most_effective_location: Optional[str]


class TemporalAnalysis(BaseModel):
    """Temporal patterns in trigger activity."""
    campaign_id: uuid.UUID

    # Hourly distribution (0-23)
    triggers_by_hour: Dict[int, int]

    # Day of week distribution (0=Monday, 6=Sunday)
    triggers_by_day_of_week: Dict[int, int]

    # Heatmap data: day_of_week -> hour -> count
    heatmap: Dict[int, Dict[int, int]]

    # Time-to-trigger distribution (in minutes, bucketed)
    time_to_trigger_distribution: Dict[str, int]  # "0-5", "5-15", "15-30", etc.

    # Time-to-trigger stats
    avg_time_to_trigger_minutes: Optional[float]
    median_time_to_trigger_minutes: Optional[float]

    # Peak times
    peak_hour: Optional[int]
    peak_day: Optional[int]  # 0=Monday

    # Daily trend
    triggers_by_date: Dict[str, int]


class LocationMetrics(BaseModel):
    """Metrics for a deployment location."""
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    drives_deployed: int
    drives_triggered: int
    trigger_rate: float
    total_triggers: int
    avg_time_to_trigger_minutes: Optional[float]


class GeographicIntelligence(BaseModel):
    """Geographic analysis of campaign activity."""
    campaign_id: uuid.UUID

    # Location-based metrics
    locations: List[LocationMetrics]

    # Trigger source analysis
    trigger_cities: Dict[str, int]
    trigger_countries: Dict[str, int]

    # Movement analysis
    drives_triggered_offsite: int  # Triggered from different location than deployed
    drives_triggered_onsite: int

    # Top performing locations
    most_effective_location: Optional[str]
    least_effective_location: Optional[str]


class BehavioralAnalysis(BaseModel):
    """Analysis of user behavior patterns."""
    campaign_id: uuid.UUID

    # Multi-file interaction
    single_file_openers: int  # IPs that opened only 1 file
    multi_file_openers: int   # IPs that opened multiple files
    avg_files_per_ip: float

    # File type preferences
    first_file_opened: Dict[str, int]  # Token type -> count of times opened first
    file_type_popularity: Dict[str, int]  # Token type -> total triggers

    # Repeat behavior
    repeat_trigger_ips: int  # IPs that triggered multiple drives
    unique_ips: int

    # User agent analysis
    os_distribution: Dict[str, int]
    browser_distribution: Dict[str, int]

    # Session patterns
    avg_session_duration_minutes: Optional[float]  # Time between first and last trigger per IP


class CampaignComparison(BaseModel):
    """Comparison metrics for a single campaign."""
    campaign_id: uuid.UUID
    campaign_name: str
    status: str
    start_date: Optional[str]
    drives_deployed: int
    drives_triggered: int
    plug_in_rate: float
    total_triggers: int
    unique_ips: int
    avg_time_to_trigger_minutes: Optional[float]


class ComparativeAnalysis(BaseModel):
    """Cross-campaign comparison and trends."""
    campaigns: List[CampaignComparison]

    # Aggregate stats
    total_campaigns: int
    avg_plug_in_rate: float
    best_campaign: Optional[str]
    worst_campaign: Optional[str]

    # Trend data (by month)
    monthly_plug_in_rates: Dict[str, float]  # "2024-01" -> rate
    monthly_trigger_counts: Dict[str, int]


class CampaignReport(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    client_name: Optional[str]
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    total_drives: int
    drives_deployed: int
    drives_triggered: int
    total_tokens: int
    total_triggers: int
    unique_source_ips: int
    first_trigger: Optional[datetime]
    last_trigger: Optional[datetime]
    drives: list


@router.get("/campaign/{campaign_id}", response_model=CampaignReport)
async def get_campaign_report(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed campaign report."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []

    # Collect stats
    total_tokens = 0
    total_triggers = 0
    unique_ips = set()
    first_trigger = None
    last_trigger = None
    drives_deployed = 0
    drives_triggered = 0

    drive_details = []

    for drive in drives:
        if drive.status.value in ["deployed", "triggered", "recovered"]:
            drives_deployed += 1
        if drive.status.value == "triggered":
            drives_triggered += 1

        tokens = drive.tokens or []
        total_tokens += len(tokens)

        drive_triggers = 0
        for token in tokens:
            triggers = token.triggers or []
            drive_triggers += len(triggers)
            total_triggers += len(triggers)

            for trigger in triggers:
                if trigger.source_ip:
                    unique_ips.add(str(trigger.source_ip))
                if first_trigger is None or trigger.triggered_at < first_trigger:
                    first_trigger = trigger.triggered_at
                if last_trigger is None or trigger.triggered_at > last_trigger:
                    last_trigger = trigger.triggered_at

        # Get deployment info
        deployment = drive.deployment
        deployment_info = None
        if deployment:
            deployment_info = {
                "location_name": deployment.location_name,
                "latitude": float(deployment.latitude) if deployment.latitude else None,
                "longitude": float(deployment.longitude) if deployment.longitude else None,
                "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else None,
            }

        drive_details.append({
            "unique_code": drive.unique_code,
            "status": drive.status.value,
            "label": drive.label,
            "token_count": len(tokens),
            "trigger_count": drive_triggers,
            "deployment": deployment_info,
            "created_at": drive.created_at.isoformat(),
        })

    return CampaignReport(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        client_name=campaign.client_name,
        status=campaign.status.value,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=campaign.end_date.isoformat() if campaign.end_date else None,
        total_drives=len(drives),
        drives_deployed=drives_deployed,
        drives_triggered=drives_triggered,
        total_tokens=total_tokens,
        total_triggers=total_triggers,
        unique_source_ips=len(unique_ips),
        first_trigger=first_trigger,
        last_trigger=last_trigger,
        drives=drive_details,
    )


@router.get("/export/{campaign_id}/csv")
async def export_campaign_csv(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export campaign data as CSV."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Drive Code", "Drive Status", "Drive Label",
        "Token Type", "Token Filename",
        "Trigger Time", "Source IP", "City", "Country", "User Agent",
        "Deployment Location", "Deployment Time"
    ])

    # Write data
    for drive in campaign.drives or []:
        deployment = drive.deployment
        dep_location = deployment.location_name if deployment else ""
        dep_time = deployment.deployed_at.isoformat() if deployment and deployment.deployed_at else ""

        for token in drive.tokens or []:
            if token.triggers:
                for trigger in token.triggers:
                    writer.writerow([
                        drive.unique_code,
                        drive.status.value,
                        drive.label or "",
                        token.token_type,
                        token.filename or "",
                        trigger.triggered_at.isoformat() if trigger.triggered_at else "",
                        str(trigger.source_ip) if trigger.source_ip else "",
                        trigger.geo_city or "",
                        trigger.geo_country or "",
                        trigger.user_agent or "",
                        dep_location,
                        dep_time,
                    ])
            else:
                # Token with no triggers
                writer.writerow([
                    drive.unique_code,
                    drive.status.value,
                    drive.label or "",
                    token.token_type,
                    token.filename or "",
                    "", "", "", "", "",
                    dep_location,
                    dep_time,
                ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={campaign.name.replace(' ', '_')}_report.csv"
        }
    )


@router.get("/summary")
async def get_summary_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system summary statistics."""
    from sqlalchemy import func
    from app.models.campaign import CampaignStatus
    from app.models.drive import DriveStatus

    # Use SQL COUNT() instead of loading all entities
    total_campaigns = db.query(func.count(Campaign.id)).scalar() or 0
    active_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.status == CampaignStatus.ACTIVE
    ).scalar() or 0
    total_drives = db.query(func.count(Drive.id)).scalar() or 0
    total_triggers = db.query(func.count(Trigger.id)).scalar() or 0

    # Get drives by status with a single query
    status_counts = db.query(
        Drive.status,
        func.count(Drive.id)
    ).group_by(Drive.status).all()

    # Convert to dict with all statuses initialized to 0
    drives_by_status = {status.value: 0 for status in DriveStatus}
    for status, count in status_counts:
        drives_by_status[status.value] = count

    return {
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "total_drives": total_drives,
        "total_triggers": total_triggers,
        "drives_by_status": drives_by_status
    }


# =============================================================================
# Executive Summary Report
# =============================================================================

@router.get("/executive-summary/{campaign_id}", response_model=ExecutiveSummary)
async def get_executive_summary(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get executive summary report for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []

    # Collect metrics
    drives_deployed = 0
    drives_triggered = 0
    total_triggers = 0
    unique_ips = set()
    first_trigger = None
    last_trigger = None
    time_to_triggers = []  # Minutes from deployment to first trigger
    profile_triggers = defaultdict(int)
    location_triggers = defaultdict(int)

    for drive in drives:
        if drive.status.value in ["deployed", "triggered", "recovered"]:
            drives_deployed += 1

        drive_first_trigger = None
        for token in (drive.tokens or []):
            for trigger in (token.triggers or []):
                total_triggers += 1
                if trigger.source_ip:
                    unique_ips.add(str(trigger.source_ip))

                if first_trigger is None or trigger.triggered_at < first_trigger:
                    first_trigger = trigger.triggered_at
                if last_trigger is None or trigger.triggered_at > last_trigger:
                    last_trigger = trigger.triggered_at

                if drive_first_trigger is None or trigger.triggered_at < drive_first_trigger:
                    drive_first_trigger = trigger.triggered_at

        if drive_first_trigger:
            drives_triggered += 1
            # Calculate time to trigger
            if drive.deployment and drive.deployment.deployed_at:
                delta = drive_first_trigger - drive.deployment.deployed_at
                time_to_triggers.append(delta.total_seconds() / 60)

            # Track by profile
            if drive.profile:
                profile_triggers[drive.profile.name] += 1

            # Track by location
            if drive.deployment and drive.deployment.location_name:
                location_triggers[drive.deployment.location_name] += 1

    # Calculate plug-in rate
    plug_in_rate = (drives_triggered / drives_deployed * 100) if drives_deployed > 0 else 0

    # Time to trigger stats
    avg_time = statistics.mean(time_to_triggers) if time_to_triggers else None
    min_time = min(time_to_triggers) if time_to_triggers else None
    max_time = max(time_to_triggers) if time_to_triggers else None

    # Calculate risk level and score
    risk_score = int(min(100, plug_in_rate * 1.2))  # Scale plug-in rate
    if risk_score >= 75:
        risk_level = "Critical"
    elif risk_score >= 50:
        risk_level = "High"
    elif risk_score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Generate key findings
    key_findings = []
    if plug_in_rate > 0:
        key_findings.append(f"{plug_in_rate:.1f}% of deployed drives were accessed by users")
    if avg_time and avg_time < 60:
        key_findings.append(f"Average time to first access was {avg_time:.0f} minutes")
    if len(unique_ips) > drives_triggered:
        key_findings.append(f"Multiple users ({len(unique_ips)} IPs) accessed the drives")
    if profile_triggers:
        top_profile = max(profile_triggers, key=profile_triggers.get)
        key_findings.append(f"'{top_profile}' profile was most effective")
    if not key_findings:
        key_findings.append("No trigger activity recorded for this campaign")

    # Most effective profile and location
    most_effective_profile = max(profile_triggers, key=profile_triggers.get) if profile_triggers else None
    most_effective_location = max(location_triggers, key=location_triggers.get) if location_triggers else None

    return ExecutiveSummary(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        client_name=campaign.client_name,
        total_drives=len(drives),
        drives_deployed=drives_deployed,
        drives_triggered=drives_triggered,
        plug_in_rate=round(plug_in_rate, 2),
        avg_time_to_trigger_minutes=round(avg_time, 2) if avg_time else None,
        min_time_to_trigger_minutes=round(min_time, 2) if min_time else None,
        max_time_to_trigger_minutes=round(max_time, 2) if max_time else None,
        risk_level=risk_level,
        risk_score=risk_score,
        key_findings=key_findings,
        campaign_start=campaign.start_date.isoformat() if campaign.start_date else None,
        campaign_end=campaign.end_date.isoformat() if campaign.end_date else None,
        first_trigger=first_trigger,
        last_trigger=last_trigger,
        total_triggers=total_triggers,
        unique_ips=len(unique_ips),
        most_effective_profile=most_effective_profile,
        most_effective_location=most_effective_location,
    )


# =============================================================================
# Temporal Analysis Report
# =============================================================================

@router.get("/temporal/{campaign_id}", response_model=TemporalAnalysis)
async def get_temporal_analysis(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get temporal analysis report for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Initialize counters
    triggers_by_hour = {i: 0 for i in range(24)}
    triggers_by_day_of_week = {i: 0 for i in range(7)}
    heatmap = {i: {j: 0 for j in range(24)} for i in range(7)}
    triggers_by_date = defaultdict(int)
    time_to_triggers = []

    for drive in (campaign.drives or []):
        deployment_time = drive.deployment.deployed_at if drive.deployment else None
        drive_first_trigger = None

        for token in (drive.tokens or []):
            for trigger in (token.triggers or []):
                if trigger.triggered_at:
                    hour = trigger.triggered_at.hour
                    day = trigger.triggered_at.weekday()
                    date_str = trigger.triggered_at.strftime("%Y-%m-%d")

                    triggers_by_hour[hour] += 1
                    triggers_by_day_of_week[day] += 1
                    heatmap[day][hour] += 1
                    triggers_by_date[date_str] += 1

                    if drive_first_trigger is None or trigger.triggered_at < drive_first_trigger:
                        drive_first_trigger = trigger.triggered_at

        # Calculate time to trigger for this drive
        if drive_first_trigger and deployment_time:
            delta = drive_first_trigger - deployment_time
            time_to_triggers.append(delta.total_seconds() / 60)

    # Time-to-trigger distribution buckets
    time_buckets = {"0-5": 0, "5-15": 0, "15-30": 0, "30-60": 0, "60-240": 0, "240+": 0}
    for minutes in time_to_triggers:
        if minutes < 5:
            time_buckets["0-5"] += 1
        elif minutes < 15:
            time_buckets["5-15"] += 1
        elif minutes < 30:
            time_buckets["15-30"] += 1
        elif minutes < 60:
            time_buckets["30-60"] += 1
        elif minutes < 240:
            time_buckets["60-240"] += 1
        else:
            time_buckets["240+"] += 1

    # Calculate stats
    avg_time = statistics.mean(time_to_triggers) if time_to_triggers else None
    median_time = statistics.median(time_to_triggers) if time_to_triggers else None

    # Find peaks
    peak_hour = max(triggers_by_hour, key=triggers_by_hour.get) if any(triggers_by_hour.values()) else None
    peak_day = max(triggers_by_day_of_week, key=triggers_by_day_of_week.get) if any(triggers_by_day_of_week.values()) else None

    return TemporalAnalysis(
        campaign_id=campaign.id,
        triggers_by_hour=triggers_by_hour,
        triggers_by_day_of_week=triggers_by_day_of_week,
        heatmap=heatmap,
        time_to_trigger_distribution=time_buckets,
        avg_time_to_trigger_minutes=round(avg_time, 2) if avg_time else None,
        median_time_to_trigger_minutes=round(median_time, 2) if median_time else None,
        peak_hour=peak_hour,
        peak_day=peak_day,
        triggers_by_date=dict(triggers_by_date),
    )


# =============================================================================
# Geographic Intelligence Report
# =============================================================================

@router.get("/geographic/{campaign_id}", response_model=GeographicIntelligence)
async def get_geographic_intelligence(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get geographic intelligence report for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Collect location metrics
    location_data = defaultdict(lambda: {
        "latitude": None,
        "longitude": None,
        "drives_deployed": 0,
        "drives_triggered": 0,
        "total_triggers": 0,
        "time_to_triggers": []
    })

    trigger_cities = defaultdict(int)
    trigger_countries = defaultdict(int)
    drives_triggered_offsite = 0
    drives_triggered_onsite = 0

    for drive in (campaign.drives or []):
        deployment = drive.deployment
        location_name = deployment.location_name if deployment else "Unknown"

        if deployment:
            location_data[location_name]["latitude"] = float(deployment.latitude) if deployment.latitude else None
            location_data[location_name]["longitude"] = float(deployment.longitude) if deployment.longitude else None

        if drive.status.value in ["deployed", "triggered", "recovered"]:
            location_data[location_name]["drives_deployed"] += 1

        drive_triggered = False
        drive_first_trigger = None

        for token in (drive.tokens or []):
            for trigger in (token.triggers or []):
                location_data[location_name]["total_triggers"] += 1

                if trigger.geo_city:
                    trigger_cities[trigger.geo_city] += 1
                if trigger.geo_country:
                    trigger_countries[trigger.geo_country] += 1

                if not drive_triggered:
                    drive_triggered = True
                    location_data[location_name]["drives_triggered"] += 1

                if drive_first_trigger is None or trigger.triggered_at < drive_first_trigger:
                    drive_first_trigger = trigger.triggered_at

                # Check if triggered from different location (offsite)
                if deployment and deployment.geo_city and trigger.geo_city:
                    if trigger.geo_city != deployment.geo_city:
                        if drive_first_trigger == trigger.triggered_at:  # Only count once per drive
                            drives_triggered_offsite += 1

        if drive_triggered:
            if deployment and deployment.deployed_at and drive_first_trigger:
                delta = drive_first_trigger - deployment.deployed_at
                location_data[location_name]["time_to_triggers"].append(delta.total_seconds() / 60)

            # If we didn't already count as offsite, count as onsite
            if deployment and deployment.geo_city:
                # Check the first trigger
                first_trigger_city = None
                for token in (drive.tokens or []):
                    for trigger in (token.triggers or []):
                        if trigger.triggered_at == drive_first_trigger:
                            first_trigger_city = trigger.geo_city
                            break
                    if first_trigger_city:
                        break

                if first_trigger_city and first_trigger_city == deployment.geo_city:
                    drives_triggered_onsite += 1

    # Build location metrics list
    locations = []
    for loc_name, data in location_data.items():
        trigger_rate = (data["drives_triggered"] / data["drives_deployed"] * 100) if data["drives_deployed"] > 0 else 0
        avg_time = statistics.mean(data["time_to_triggers"]) if data["time_to_triggers"] else None

        locations.append(LocationMetrics(
            location_name=loc_name if loc_name != "Unknown" else None,
            latitude=data["latitude"],
            longitude=data["longitude"],
            drives_deployed=data["drives_deployed"],
            drives_triggered=data["drives_triggered"],
            trigger_rate=round(trigger_rate, 2),
            total_triggers=data["total_triggers"],
            avg_time_to_trigger_minutes=round(avg_time, 2) if avg_time else None,
        ))

    # Sort by trigger rate descending
    locations.sort(key=lambda x: x.trigger_rate, reverse=True)

    # Find most/least effective
    effective_locations = [l for l in locations if l.drives_deployed > 0]
    most_effective = effective_locations[0].location_name if effective_locations else None
    least_effective = effective_locations[-1].location_name if effective_locations else None

    return GeographicIntelligence(
        campaign_id=campaign.id,
        locations=locations,
        trigger_cities=dict(trigger_cities),
        trigger_countries=dict(trigger_countries),
        drives_triggered_offsite=drives_triggered_offsite,
        drives_triggered_onsite=drives_triggered_onsite,
        most_effective_location=most_effective,
        least_effective_location=least_effective,
    )


# =============================================================================
# Behavioral Analysis Report
# =============================================================================

def parse_user_agent(ua_string: str) -> tuple:
    """Extract OS and browser from user agent string."""
    if not ua_string:
        return "Unknown", "Unknown"

    ua_lower = ua_string.lower()

    # Detect OS
    if "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower or "darwin" in ua_lower:
        os = "macOS"
    elif "linux" in ua_lower:
        os = "Linux"
    elif "android" in ua_lower:
        os = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os = "iOS"
    else:
        os = "Other"

    # Detect browser
    if "edg" in ua_lower:
        browser = "Edge"
    elif "chrome" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
    else:
        browser = "Other"

    return os, browser


@router.get("/behavioral/{campaign_id}", response_model=BehavioralAnalysis)
async def get_behavioral_analysis(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get behavioral analysis report for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Track by IP
    ip_files = defaultdict(set)  # IP -> set of token types opened
    ip_triggers = defaultdict(list)  # IP -> list of trigger times
    ip_drives = defaultdict(set)  # IP -> set of drive IDs

    # Track file type popularity
    first_file_opened = defaultdict(int)
    file_type_popularity = defaultdict(int)

    # Track user agents
    os_distribution = defaultdict(int)
    browser_distribution = defaultdict(int)

    for drive in (campaign.drives or []):
        drive_first_trigger = None
        drive_first_token_type = None

        for token in (drive.tokens or []):
            for trigger in (token.triggers or []):
                ip = str(trigger.source_ip) if trigger.source_ip else "unknown"

                ip_files[ip].add(token.token_type)
                ip_triggers[ip].append(trigger.triggered_at)
                ip_drives[ip].add(str(drive.id))

                file_type_popularity[token.token_type] += 1

                # Track first file opened per drive
                if drive_first_trigger is None or trigger.triggered_at < drive_first_trigger:
                    drive_first_trigger = trigger.triggered_at
                    drive_first_token_type = token.token_type

                # Parse user agent
                if trigger.user_agent:
                    os, browser = parse_user_agent(trigger.user_agent)
                    os_distribution[os] += 1
                    browser_distribution[browser] += 1

        if drive_first_token_type:
            first_file_opened[drive_first_token_type] += 1

    # Calculate metrics
    unique_ips = len(ip_files)
    single_file_openers = sum(1 for files in ip_files.values() if len(files) == 1)
    multi_file_openers = sum(1 for files in ip_files.values() if len(files) > 1)

    total_files_opened = sum(len(files) for files in ip_files.values())
    avg_files_per_ip = total_files_opened / unique_ips if unique_ips > 0 else 0

    # IPs that triggered multiple drives
    repeat_trigger_ips = sum(1 for drives in ip_drives.values() if len(drives) > 1)

    # Calculate session durations
    session_durations = []
    for ip, times in ip_triggers.items():
        if len(times) > 1:
            sorted_times = sorted(times)
            duration = (sorted_times[-1] - sorted_times[0]).total_seconds() / 60
            session_durations.append(duration)

    avg_session_duration = statistics.mean(session_durations) if session_durations else None

    return BehavioralAnalysis(
        campaign_id=campaign.id,
        single_file_openers=single_file_openers,
        multi_file_openers=multi_file_openers,
        avg_files_per_ip=round(avg_files_per_ip, 2),
        first_file_opened=dict(first_file_opened),
        file_type_popularity=dict(file_type_popularity),
        repeat_trigger_ips=repeat_trigger_ips,
        unique_ips=unique_ips,
        os_distribution=dict(os_distribution),
        browser_distribution=dict(browser_distribution),
        avg_session_duration_minutes=round(avg_session_duration, 2) if avg_session_duration else None,
    )


# =============================================================================
# Comparative Analysis Report (Cross-Campaign)
# =============================================================================

@router.get("/comparative", response_model=ComparativeAnalysis)
async def get_comparative_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comparative analysis across all campaigns."""
    campaigns = db.query(Campaign).options(
        joinedload(Campaign.drives)
    ).all()

    campaign_comparisons = []
    monthly_data = defaultdict(lambda: {"triggers": 0, "deployed": 0, "triggered": 0})

    for campaign in campaigns:
        drives_deployed = 0
        drives_triggered = 0
        total_triggers = 0
        unique_ips = set()
        time_to_triggers = []

        for drive in (campaign.drives or []):
            if drive.status.value in ["deployed", "triggered", "recovered"]:
                drives_deployed += 1

            drive_first_trigger = None
            for token in (drive.tokens or []):
                for trigger in (token.triggers or []):
                    total_triggers += 1
                    if trigger.source_ip:
                        unique_ips.add(str(trigger.source_ip))

                    if drive_first_trigger is None or trigger.triggered_at < drive_first_trigger:
                        drive_first_trigger = trigger.triggered_at

                    # Track monthly triggers
                    if trigger.triggered_at:
                        month_key = trigger.triggered_at.strftime("%Y-%m")
                        monthly_data[month_key]["triggers"] += 1

            if drive_first_trigger:
                drives_triggered += 1
                if drive.deployment and drive.deployment.deployed_at:
                    delta = drive_first_trigger - drive.deployment.deployed_at
                    time_to_triggers.append(delta.total_seconds() / 60)

        # Track monthly deployed/triggered
        if campaign.start_date:
            month_key = campaign.start_date.strftime("%Y-%m")
            monthly_data[month_key]["deployed"] += drives_deployed
            monthly_data[month_key]["triggered"] += drives_triggered

        plug_in_rate = (drives_triggered / drives_deployed * 100) if drives_deployed > 0 else 0
        avg_time = statistics.mean(time_to_triggers) if time_to_triggers else None

        campaign_comparisons.append(CampaignComparison(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            status=campaign.status.value,
            start_date=campaign.start_date.isoformat() if campaign.start_date else None,
            drives_deployed=drives_deployed,
            drives_triggered=drives_triggered,
            plug_in_rate=round(plug_in_rate, 2),
            total_triggers=total_triggers,
            unique_ips=len(unique_ips),
            avg_time_to_trigger_minutes=round(avg_time, 2) if avg_time else None,
        ))

    # Sort by plug-in rate descending
    campaign_comparisons.sort(key=lambda x: x.plug_in_rate, reverse=True)

    # Calculate aggregate stats
    rates = [c.plug_in_rate for c in campaign_comparisons if c.drives_deployed > 0]
    avg_plug_in_rate = statistics.mean(rates) if rates else 0

    best_campaign = campaign_comparisons[0].campaign_name if campaign_comparisons and campaign_comparisons[0].drives_deployed > 0 else None
    worst_campaign = None
    for c in reversed(campaign_comparisons):
        if c.drives_deployed > 0:
            worst_campaign = c.campaign_name
            break

    # Calculate monthly rates
    monthly_plug_in_rates = {}
    monthly_trigger_counts = {}
    for month, data in sorted(monthly_data.items()):
        monthly_trigger_counts[month] = data["triggers"]
        if data["deployed"] > 0:
            monthly_plug_in_rates[month] = round(data["triggered"] / data["deployed"] * 100, 2)
        else:
            monthly_plug_in_rates[month] = 0

    return ComparativeAnalysis(
        campaigns=campaign_comparisons,
        total_campaigns=len(campaigns),
        avg_plug_in_rate=round(avg_plug_in_rate, 2),
        best_campaign=best_campaign,
        worst_campaign=worst_campaign,
        monthly_plug_in_rates=monthly_plug_in_rates,
        monthly_trigger_counts=monthly_trigger_counts,
    )
