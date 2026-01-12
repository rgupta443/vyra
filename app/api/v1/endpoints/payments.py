"""
Payment processing endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/create-checkout")
async def create_checkout():
    """Create Stripe checkout session."""
    return {"message": "Checkout creation endpoint - to be implemented"}


@router.post("/webhook")
async def stripe_webhook():
    """Handle Stripe webhooks."""
    return {"message": "Stripe webhook endpoint - to be implemented"}


@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    return {"message": "Plans endpoint - to be implemented"}