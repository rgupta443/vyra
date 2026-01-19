"""
Generation-related Pydantic schemas for request/response models.
"""
from typing import Optional, List, Any
from pydantic import BaseModel, field_serializer, model_serializer
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
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to handle UUID conversion."""
        return {
            'id': str(self.id) if isinstance(self.id, UUID) else self.id,
            'user_id': str(self.user_id) if isinstance(self.user_id, UUID) else self.user_id,
            'face_id': str(self.face_id) if isinstance(self.face_id, UUID) else self.face_id,
            'preset_type': self.preset_type,
            'format_type': self.format_type,
            'status': self.status,
            'image_url': self.image_url,
            'caption': self.caption,
            'hashtags': self.hashtags,
            'location': self.location,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }
    
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
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to handle UUID conversion."""
        return {
            'id': str(self.id) if isinstance(self.id, UUID) else self.id,
            'status': self.status,
            'image_url': self.image_url,
            'caption': self.caption,
            'hashtags': self.hashtags,
            'location': self.location,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }
    
    class Config:
        from_attributes = True


class InsufficientCreditsError(BaseModel):
    """Schema for insufficient credits error."""
    detail: str
    credits_required: int
    current_credits: int