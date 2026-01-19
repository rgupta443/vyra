"""
Generation-related Pydantic schemas for request/response models.
"""
from typing import Optional, List
from pydantic import BaseModel, field_serializer
from datetime import datetime
from uuid import UUID

from app.models.generation import PresetType, FormatType, GenerationStatus


class GenerationRequest(BaseModel):
    """Schema for generation request."""
    preset_type: PresetType
    format_type: FormatType


class GenerationResponse(BaseModel):
    """Schema for generation response."""
    id: str
    user_id: str
    face_id: str
    preset_type: PresetType
    format_type: FormatType
    status: GenerationStatus
    image_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    location: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    @field_serializer('id', 'user_id', 'face_id')
    def serialize_uuid(self, value):
        """Convert UUID to string."""
        if isinstance(value, UUID):
            return str(value)
        return value
    
    class Config:
        from_attributes = True


class GenerationStatusResponse(BaseModel):
    """Schema for generation status response."""
    id: str
    status: GenerationStatus
    image_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    location: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    @field_serializer('id')
    def serialize_uuid(self, value):
        """Convert UUID to string."""
        if isinstance(value, UUID):
            return str(value)
        return value
    
    class Config:
        from_attributes = True


class InsufficientCreditsError(BaseModel):
    """Schema for insufficient credits error."""
    detail: str
    credits_required: int
    current_credits: int