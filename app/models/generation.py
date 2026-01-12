"""
Generation model definition for tracking content generation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PresetType(str, Enum):
    """Content generation preset types."""
    LUXURY = "luxury"
    LIFESTYLE = "lifestyle"
    BEAUTY = "beauty"


class FormatType(str, Enum):
    """Instagram format types."""
    REEL_9_16 = "reel_9_16"
    FEED_4_5 = "feed_4_5"
    SQUARE_1_1 = "square_1_1"


class GenerationStatus(str, Enum):
    """Generation job status types."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Generation(Base):
    """Generation model for tracking content generation requests and results."""
    __tablename__ = "generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    face_id = Column(UUID(as_uuid=True), ForeignKey("faces.id"), nullable=False)
    
    preset_type = Column(String, nullable=False)
    format_type = Column(String, nullable=False)
    status = Column(String, default=GenerationStatus.PENDING.value)
    
    # Results
    image_url = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    location = Column(String, nullable=True)
    
    # Metadata
    job_id = Column(String, nullable=True)  # Queue job ID
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generations")
    face = relationship("Face", back_populates="generations")