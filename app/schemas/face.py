"""
Pydantic schemas for face-related operations.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class FaceUploadResponse(BaseModel):
    """Response schema for face upload."""
    id: UUID
    image_url: str
    identity_strength: float
    is_active: bool
    created_at: datetime
    message: str = "Face uploaded successfully"
    
    class Config:
        from_attributes = True


class FaceInfo(BaseModel):
    """Schema for face information."""
    id: UUID
    image_url: str
    identity_strength: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FaceValidationResult(BaseModel):
    """Schema for face validation results."""
    is_valid: bool
    quality_score: float
    face_detected: bool
    validation_errors: list[str] = []
    metadata: dict = {}


class FaceDeleteResponse(BaseModel):
    """Response schema for face deletion."""
    message: str = "Face deleted successfully"
    deleted_face_id: UUID