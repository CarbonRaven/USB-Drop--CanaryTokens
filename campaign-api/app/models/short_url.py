"""ShortUrl model - URL shortener integration via Shlink."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ShortUrl(Base):
    """Short URL mapping for token tracking via Shlink."""

    __tablename__ = "short_urls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("drives.id", ondelete="CASCADE"), nullable=False)
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False)

    # Position index for multiple URLs per token (0-based)
    position = Column(Integer, nullable=False, default=0)

    # URL slug components
    base_slug = Column(String(100), nullable=False)       # e.g., "hr-docs"
    suffix_mode = Column(String(20), nullable=False)      # random, sequential, drive_code, custom
    generated_suffix = Column(String(50), nullable=False) # e.g., "x7k2", "001", "USB-A1B2C3"
    full_slug = Column(String(150), nullable=False)       # e.g., "hr-docs-x7k2"

    # Shlink data
    shlink_short_code = Column(String(50), nullable=False, index=True)
    shlink_domain = Column(String(255), nullable=False)

    # URLs
    canary_url = Column(Text, nullable=False)  # Original CanaryTokens URL
    short_url = Column(Text, nullable=False)   # Final shortened URL

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    drive = relationship("Drive", back_populates="short_urls")
    token = relationship("Token", back_populates="short_urls")


# Example usage:
# - Drive USB-A1B2C3 is created from profile "HR Leak"
# - Profile has url_config: {"base_slug": "hr-docs", "suffix_mode": "random"}
# - When tokens are created, ShortUrl records are generated:
#   - ShortUrl(base_slug="hr-docs", suffix_mode="random", generated_suffix="x7k2",
#              full_slug="hr-docs-x7k2", short_url="https://links.example.com/hr-docs-x7k2")
