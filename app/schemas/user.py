"""
User-related Pydantic schemas for request/response models.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.user import PlanType


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: str


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    plan_type: PlanType
    credits: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreditBalance(BaseModel):
    """Schema for credit balance response."""
    credits: int
    plan_type: PlanType


class PlanUpdate(BaseModel):
    """Schema for plan update request."""
    plan_type: PlanType


class CreditUpdate(BaseModel):
    """Schema for credit update request."""
    amount: int