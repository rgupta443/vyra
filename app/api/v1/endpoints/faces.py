"""
Face management endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_face():
    """Upload face image."""
    return {"message": "Face upload endpoint - to be implemented"}


@router.get("/current")
async def get_current_face():
    """Get current active face."""
    return {"message": "Current face endpoint - to be implemented"}


@router.delete("/current")
async def delete_current_face():
    """Delete current active face."""
    return {"message": "Delete face endpoint - to be implemented"}