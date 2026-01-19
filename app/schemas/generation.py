"""
Generation-related Pydantic schemas for request/response models.
"""
from typing import Optional, List, Union
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

from app.models.generation import PresetType, FormatType, GenerationStatus


class GenerationRequest(BaseModel):
    """Schema for generation request."""
    preset_type: PresetType
    format_type: FormatType


class GenerationResponse(BaseModel):
    """Schema for generation response."""
    id: Union[str, UUID]
    user_id: Union[str, UUID]
    face_id: Union[str, UUID]
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
    
    @field_validator('id', 'user_id', 'face_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string."""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class GenerationStatusResponse(BaseModel):
    """Schema for generation status response."""
    id: Union[str, UUID]
    status: GenerationStatus
    image_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    location: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string."""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class InsufficientCreditsError(BaseModel):
    """Schema for insufficient credits error."""
    detail: str
    credits_required: int
    current_credits: int