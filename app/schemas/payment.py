"""
Payment-related Pydantic schemas for request/response models.
"""
from typing import Optional
from pydantic import BaseModel
from app.models.user import PlanType


class CheckoutRequest(BaseModel):
    """Schema for creating a Stripe checkout session."""
    plan_type: PlanType
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Schema for checkout session response."""
    session_id: str
    url: str


class PlanInfo(BaseModel):
    """Schema for subscription plan information."""
    plan_type: PlanType
    name: str
    price: int  # Price in cents
    credits: int
    description: str
    stripe_price_id: Optional[str] = None


class WebhookEvent(BaseModel):
    """Schema for Stripe webhook event."""
    type: str
    data: dict
