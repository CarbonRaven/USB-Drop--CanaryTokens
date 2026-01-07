"""Target model - Organization profiles for targeted campaigns."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


# Industry choices
INDUSTRIES = [
    "healthcare",
    "finance",
    "technology",
    "manufacturing",
    "retail",
    "government",
    "education",
    "legal",
    "energy",
    "telecommunications",
    "media",
    "consulting",
    "nonprofit",
    "other",
]

# Company size choices
COMPANY_SIZES = [
    "startup",      # < 50 employees
    "smb",          # 50-200 employees
    "mid_market",   # 200-1000 employees
    "enterprise",   # 1000+ employees
]

# Target department choices
DEPARTMENTS = [
    "it",
    "hr",
    "finance",
    "executive",
    "engineering",
    "sales",
    "marketing",
    "operations",
    "legal",
    "research",
    "general",
]

# Geographic regions
REGIONS = [
    "us_east",
    "us_west",
    "us_central",
    "canada",
    "uk",
    "eu_west",
    "eu_east",
    "apac",
    "latam",
    "middle_east",
    "africa",
    "global",
]


class Target(Base):
    """Target organization profile for a campaign."""

    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(255), nullable=False)  # Internal reference name
    company_name = Column(String(255), nullable=False)  # Actual company name

    # Classification
    industry = Column(String(50), nullable=False, default="other")
    company_size = Column(String(50), nullable=False, default="mid_market")
    target_department = Column(String(50), nullable=True)
    geographic_region = Column(String(50), nullable=True, default="us_east")

    # Technical context
    known_technologies = Column(JSON, default=list)  # ["AWS", "Office 365", "SAP"]
    email_domain = Column(String(255), nullable=True)  # @acme.com

    # OSINT and research
    osint_notes = Column(Text, nullable=True)  # Free-form research notes
    website = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # AI-generated recommendations (cached)
    recommended_scenario = Column(String(50), nullable=True)
    scenario_reasoning = Column(Text, nullable=True)
    suggested_labels = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="target")

    def __repr__(self):
        return f"<Target {self.name} ({self.company_name})>"
