"""
Content generation endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.face import Face
from app.services.generation_service import GenerationService
from app.services.user_service import UserService
from app.services.plan_service import PlanService
from app.schemas.generation import (
    GenerationRequest,
    GenerationResponse,
    GenerationStatusResponse,
    InsufficientCreditsError
)

router = APIRouter()


@router.post("/image", response_model=GenerationResponse)
async def generate_image(
    request: GenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate Instagram image."""
    # Check if user has an active face
    active_face = db.query(Face).filter(
        Face.user_id == current_user.id,
        Face.is_active == True
    ).first()
    
    if not active_face:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active face found. Please upload a face first."
        )
    
    # Check if user has credits and plan allows generation
    can_generate, restriction_message = GenerationService.can_generate(db, str(current_user.id))
    if not can_generate:
        current_credits = UserService.get_credit_balance(db, str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": restriction_message,
                "credits_required": 1,
                "current_credits": current_credits,
                "upgrade_message": PlanService.get_upgrade_message(PlanType(current_user.plan_type))
            }
        )
    
    # Create generation and deduct credit
    generation, error_message = GenerationService.create_generation(
        db=db,
        user_id=str(current_user.id),
        face_id=str(active_face.id),
        preset_type=request.preset_type,
        format_type=request.format_type
    )
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message or "Failed to create generation request"
        )
    
    # TODO: Queue the generation job here
    # For now, just return the pending generation
    return generation


@router.get("/status/{generation_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generation job status."""
    generation = GenerationService.get_generation_by_id(db, generation_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    # Ensure user owns this generation
    if str(generation.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return generation


@router.get("/history", response_model=List[GenerationResponse])
async def get_generation_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's generation history."""
    generations = GenerationService.get_user_generations(
        db=db,
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )
    return generations