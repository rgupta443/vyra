"""
User management endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/profile")
async def get_profile():
    """Get user profile."""
    return {"message": "Profile endpoint - to be implemented"}


@router.put("/profile")
async def update_profile():
    """Update user profile."""
    return {"message": "Update profile endpoint - to be implemented"}


@router.get("/credits")
async def get_credits():
    """Get user credit balance."""
    return {"message": "Credits endpoint - to be implemented"}