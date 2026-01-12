"""
Preset configuration model definition.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PresetConfig(Base):
    """Preset configuration model for generation templates."""
    __tablename__ = "preset_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    
    prompt_template = Column(String, nullable=False)
    style_parameters = Column(JSON, nullable=False)  # Dict of style parameters
    brand_safety_rules = Column(JSON, nullable=False)  # List of safety rules
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)