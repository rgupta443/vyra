"""
Plan enforcement service for subscription plan management.
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User, PlanType
from app.services.user_service import UserService


class PlanService:
    """Service class for plan enforcement and management."""
    
    # Plan limits and features
    PLAN_LIMITS = {
        PlanType.FREE: {
            "monthly_generations": 5,
            "max_faces": 1,
            "priority_queue": False,
            "advanced_presets": False
        },
        PlanType.BASIC: {
            "monthly_generations": 100,
            "max_faces": 3,
            "priority_queue": False,
            "advanced_presets": True
        },
        PlanType.PRO: {
            "monthly_generations": 500,
            "max_faces": 10,
            "priority_queue": True,
            "advanced_presets": True
        }
    }
    
    @staticmethod
    def get_plan_limits(plan_type: PlanType) -> Dict:
        """Get limits for a specific plan."""
        return PlanService.PLAN_LIMITS.get(plan_type, PlanService.PLAN_LIMITS[PlanType.FREE])
    
    @staticmethod
    def can_generate(db: Session, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can generate content based on plan limits.
        Returns (can_generate, restriction_message).
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        plan_type = PlanType(user.plan_type)
        
        # Check credit balance first
        if user.credits <= 0:
            if plan_type == PlanType.FREE:
                return False, "You've used all your free generations. Upgrade to continue creating content."
            else:
                return False, "You've used all your monthly generations. Your credits will reset next month."
        
        return True, None
    
    @staticmethod
    def can_upload_face(db: Session, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can upload a new face based on plan limits.
        Returns (can_upload, restriction_message).
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        plan_type = PlanType(user.plan_type)
        plan_limits = PlanService.get_plan_limits(plan_type)
        
        # Count current faces
        current_faces = len([face for face in user.faces if face.is_active])
        
        if current_faces >= plan_limits["max_faces"]:
            if plan_type == PlanType.FREE:
                return False, "Free plan allows only 1 face. Upgrade to upload more faces."
            else:
                return False, f"Your {plan_type.value} plan allows up to {plan_limits['max_faces']} faces."
        
        return True, None
    
    @staticmethod
    def get_upgrade_message(current_plan: PlanType) -> str:
        """Get upgrade message for current plan."""
        if current_plan == PlanType.FREE:
            return "Upgrade to Basic for 100 monthly generations and advanced presets, or Pro for 500 generations and priority processing."
        elif current_plan == PlanType.BASIC:
            return "Upgrade to Pro for 500 monthly generations, priority processing, and up to 10 faces."
        else:
            return "You're on our highest plan with unlimited features!"
    
    @staticmethod
    def handle_plan_downgrade(db: Session, user_id: str, new_plan: PlanType) -> tuple[bool, Optional[str]]:
        """
        Handle plan downgrade gracefully.
        Returns (success, message).
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        current_plan = PlanType(user.plan_type)
        new_limits = PlanService.get_plan_limits(new_plan)
        
        # Check if downgrade is possible
        current_faces = len([face for face in user.faces if face.is_active])
        if current_faces > new_limits["max_faces"]:
            return False, f"Cannot downgrade: You have {current_faces} faces but {new_plan.value} plan allows only {new_limits['max_faces']}. Please remove some faces first."
        
        # Update plan and reset credits
        UserService.update_plan(db, user_id, new_plan)
        
        return True, f"Successfully downgraded to {new_plan.value} plan. Your credits have been reset to {UserService.PLAN_CREDITS[new_plan]}."
    
    @staticmethod
    def get_plan_features(plan_type: PlanType) -> Dict:
        """Get feature list for a plan."""
        limits = PlanService.get_plan_limits(plan_type)
        credits = UserService.PLAN_CREDITS[plan_type]
        
        return {
            "plan_name": plan_type.value.title(),
            "monthly_credits": credits,
            "monthly_generations": limits["monthly_generations"],
            "max_faces": limits["max_faces"],
            "priority_queue": limits["priority_queue"],
            "advanced_presets": limits["advanced_presets"],
            "features": [
                f"{credits} monthly generations",
                f"Up to {limits['max_faces']} face{'s' if limits['max_faces'] > 1 else ''}",
                "Basic presets (Luxury, Lifestyle, Beauty)" if not limits["advanced_presets"] else "All presets including advanced options",
                "Standard processing" if not limits["priority_queue"] else "Priority queue processing"
            ]
        }
    
    @staticmethod
    def enforce_plan_restrictions(db: Session, user_id: str, action: str) -> tuple[bool, Optional[str]]:
        """
        Enforce plan restrictions for various actions.
        Actions: 'generate', 'upload_face', 'advanced_preset'
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        plan_type = PlanType(user.plan_type)
        
        if action == "generate":
            return PlanService.can_generate(db, user_id)
        elif action == "upload_face":
            return PlanService.can_upload_face(db, user_id)
        elif action == "advanced_preset":
            limits = PlanService.get_plan_limits(plan_type)
            if not limits["advanced_presets"]:
                return False, "Advanced presets are available with Basic and Pro plans. Upgrade to access more preset options."
            return True, None
        
        return True, None