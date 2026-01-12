"""
Content generation endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/image")
async def generate_image():
    """Generate Instagram image."""
    return {"message": "Image generation endpoint - to be implemented"}


@router.get("/status/{job_id}")
async def get_generation_status(job_id: str):
    """Get generation job status."""
    return {"message": f"Generation status for {job_id} - to be implemented"}


@router.get("/history")
async def get_generation_history():
    """Get user's generation history."""
    return {"message": "Generation history endpoint - to be implemented"}