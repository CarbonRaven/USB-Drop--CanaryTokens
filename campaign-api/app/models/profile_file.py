"""ProfileFile model - uploaded files for profiles."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ProfileFile(Base):
    """Uploaded file associated with a profile."""

    __tablename__ = "profile_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)

    # File identification
    filename = Column(String(255), nullable=False)          # Original filename
    stored_filename = Column(String(255), nullable=False)   # UUID-based storage name
    folder = Column(String(255), default="")                # Target folder in profile

    # File type classification
    file_type = Column(String(50), nullable=False)          # 'document', 'static', 'shortcut', 'template'
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Token configuration (for documents that get tokens embedded)
    token_type = Column(String(50), nullable=True)          # 'ms_word', 'ms_excel', 'pdf', None for static
    token_config = Column(JSONB, default=dict)              # Additional token options

    # For shortcut files (.url, .webloc)
    target_url = Column(String(1000), nullable=True)
    shortcut_type = Column(String(20), nullable=True)       # 'windows', 'macos', 'both'

    # For custom text content/templates
    custom_content = Column(Text, nullable=True)            # Custom template content with placeholders

    # Display order
    sort_order = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="uploaded_files")


# File types:
# - 'document': Word, Excel, PDF files that can have tokens embedded
# - 'static': Images (PNG, JPG, GIF) included as-is without tokens
# - 'shortcut': URL shortcut files (.url for Windows, .webloc for macOS)
# - 'template': Custom text templates with {canary_url} placeholders

# Token types for documents:
# - 'ms_word': Word document with embedded web bug
# - 'ms_excel': Excel spreadsheet with external data connection
# - 'pdf': PDF with embedded tracking

# Shortcut types:
# - 'windows': Creates .url file (INI format)
# - 'macos': Creates .webloc file (XML plist)
# - 'both': Creates both .url and .webloc files
