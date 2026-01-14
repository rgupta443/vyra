"""
User management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, PlanType
from app.services.user_service import UserService
from app.schemas.user import UserResponse, CreditBalance, PlanUpdate, CreditUpdate

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile."""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    # For now, just return current user - can be extended later
    return current_user


@router.get("/credits", response_model=CreditBalance)
async def get_credits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user credit balance."""
    return CreditBalance(
        credits=current_user.credits,
        plan_type=PlanType(current_user.plan_type)
    )


@router.put("/plan", response_model=UserResponse)
async def update_plan(
    plan_update: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's subscription plan."""
    updated_user = UserService.update_plan(db, str(current_user.id), plan_update.plan_type)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.post("/credits/add", response_model=UserResponse)
async def add_credits(
    credit_update: CreditUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add credits to user's balance (admin function)."""
    if credit_update.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit amount must be positive"
        )
    
    updated_user = UserService.add_credits(db, str(current_user.id), credit_update.amount)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user