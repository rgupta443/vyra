"""
Plan management endpoints.
"""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, PlanType
from app.services.plan_service import PlanService
from app.services.user_service import UserService
from app.schemas.user import PlanUpdate, UserResponse

router = APIRouter()


@router.get("/features")
async def get_all_plan_features() -> Dict[str, Dict]:
    """Get features for all available plans."""
    return {
        plan.value: PlanService.get_plan_features(plan)
        for plan in PlanType
    }


@router.get("/current")
async def get_current_plan_features(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get features for user's current plan."""
    plan_type = PlanType(current_user.plan_type)
    return PlanService.get_plan_features(plan_type)


@router.put("/upgrade", response_model=UserResponse)
async def upgrade_plan(
    plan_update: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade user's subscription plan."""
    current_plan = PlanType(current_user.plan_type)
    new_plan = plan_update.plan_type
    
    # Prevent downgrades through this endpoint
    plan_hierarchy = {PlanType.FREE: 0, PlanType.BASIC: 1, PlanType.PRO: 2}
    if plan_hierarchy[new_plan] <= plan_hierarchy[current_plan]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the downgrade endpoint for plan downgrades"
        )
    
    # Update plan
    updated_user = UserService.update_plan(db, str(current_user.id), new_plan)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.put("/downgrade", response_model=UserResponse)
async def downgrade_plan(
    plan_update: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Downgrade user's subscription plan with validation."""
    current_plan = PlanType(current_user.plan_type)
    new_plan = plan_update.plan_type
    
    # Prevent upgrades through this endpoint
    plan_hierarchy = {PlanType.FREE: 0, PlanType.BASIC: 1, PlanType.PRO: 2}
    if plan_hierarchy[new_plan] >= plan_hierarchy[current_plan]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the upgrade endpoint for plan upgrades"
        )
    
    # Handle downgrade with validation
    success, message = PlanService.handle_plan_downgrade(db, str(current_user.id), new_plan)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Get updated user
    updated_user = UserService.get_user_by_id(db, str(current_user.id))
    return updated_user


@router.get("/restrictions")
async def check_plan_restrictions(
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can perform a specific action based on their plan.
    Actions: 'generate', 'upload_face', 'advanced_preset'
    """
    valid_actions = ['generate', 'upload_face', 'advanced_preset']
    if action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Valid actions: {', '.join(valid_actions)}"
        )
    
    can_perform, restriction_message = PlanService.enforce_plan_restrictions(
        db, str(current_user.id), action
    )
    
    return {
        "action": action,
        "allowed": can_perform,
        "message": restriction_message,
        "current_plan": current_user.plan_type,
        "upgrade_message": PlanService.get_upgrade_message(PlanType(current_user.plan_type)) if not can_perform else None
    }