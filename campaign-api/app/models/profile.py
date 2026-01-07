"""Profile model - USB drive templates."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Profile(Base):
    """USB drive profile template."""

    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scenario categorization
    scenario_type = Column(String(50), nullable=False)  # hr, it, executive, creator, etc.
    theme = Column(String(50), nullable=True)

    # Template configuration (JSON)
    file_structure = Column(JSONB, default=dict)  # Files/folders to create
    token_config = Column(JSONB, default=dict)    # Token types and placement
    ai_prompts = Column(JSONB, default=dict)      # Prompts for AI content generation
    url_config = Column(JSONB, default=dict)      # Short URL configuration

    # Suggested USB drive labels
    label_suggestions = Column(ARRAY(String), default=list)

    # Metadata
    is_system = Column(String(10), default="false")  # Built-in vs user-created
    is_active = Column(Boolean, default=True, nullable=False)  # Enable/disable profile
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drives = relationship("Drive", back_populates="profile")
    generated_content = relationship("GeneratedContent", back_populates="profile")
    uploaded_files = relationship("ProfileFile", back_populates="profile", cascade="all, delete-orphan")


# Example file_structure JSONB:
# {
#     "folders": ["HR Documents", "Payroll", "Benefits"],
#     "files": [
#         {"name": "Employee_Salaries_2024.xlsx", "type": "excel_token", "folder": "Payroll"},
#         {"name": "Benefits_Overview.docx", "type": "word_token", "folder": "Benefits"},
#         {"name": "HR_Contacts.pdf", "type": "pdf_token", "folder": "HR Documents"},
#         {"name": "desktop.ini", "type": "folder_token", "folder": "HR Documents"}
#     ]
# }

# Example token_config JSONB:
# {
#     "tokens": [
#         {"type": "doc-msword", "count": 2, "redirect_theme": "corporate"},
#         {"type": "doc-msexcel", "count": 1, "redirect_theme": "login"},
#         {"type": "windows-dir", "count": 1},
#         {"type": "qr-code", "count": 1, "filename": "WiFi_Password.png"}
#     ]
# }

# Example ai_prompts JSONB:
# {
#     "document_content": "Create a professional HR document about employee benefits...",
#     "image_prompt": "Corporate office setting, professional environment, business casual..."
# }

# Example url_config JSONB:
# {
#     "enabled": true,
#     "base_slug": "hr-docs",
#     "suffix_mode": "random",  # random, sequential, drive_code, custom
#     "suffix_length": 4,       # For random mode
#     "domain": "links.example.com"  # Optional, uses default if not set
# }
