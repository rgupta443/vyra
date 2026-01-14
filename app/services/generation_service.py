"""
Generation service for content generation operations.
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.generation import Generation, GenerationStatus, PresetType, FormatType
from app.models.user import User
from app.services.user_service import UserService
from app.services.plan_service import PlanService


class GenerationService:
    """Service class for generation-related operations."""
    
    @staticmethod
    def can_generate(db: Session, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can generate content (has credits and plan allows).
        Returns (can_generate, restriction_message).
        """
        # Check plan restrictions first
        can_generate, message = PlanService.can_generate(db, user_id)
        if not can_generate:
            return False, message
        
        # Check credits
        if not UserService.has_credits(db, user_id):
            return False, "Insufficient credits for generation"
        
        return True, None
    
    @staticmethod
    def create_generation(
        db: Session,
        user_id: str,
        face_id: str,
        preset_type: PresetType,
        format_type: FormatType
    ) -> tuple[Optional[Generation], Optional[str]]:
        """
        Create a new generation request and deduct credit.
        Returns (generation, error_message).
        """
        # Check plan restrictions
        can_generate, restriction_message = GenerationService.can_generate(db, user_id)
        if not can_generate:
            return None, restriction_message
        
        # Deduct credit first
        if not UserService.deduct_credit(db, user_id):
            return None, "Failed to deduct credit"
        
        try:
            # Create generation record
            generation = Generation(
                user_id=user_id,
                face_id=face_id,
                preset_type=preset_type.value,
                format_type=format_type.value,
                status=GenerationStatus.PENDING.value
            )
            db.add(generation)
            db.commit()
            db.refresh(generation)
            return generation, None
        except Exception as e:
            # If generation creation fails, refund the credit
            UserService.refund_credit(db, user_id)
            db.rollback()
            return None, f"Failed to create generation: {str(e)}"
    
    @staticmethod
    def update_generation_status(
        db: Session,
        generation_id: str,
        status: GenerationStatus,
        error_message: Optional[str] = None
    ) -> Optional[Generation]:
        """Update generation status."""
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return None
        
        generation.status = status.value
        if error_message:
            generation.error_message = error_message
        
        if status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
            generation.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(generation)
        return generation
    
    @staticmethod
    def complete_generation(
        db: Session,
        generation_id: str,
        image_url: str,
        caption: Optional[str] = None,
        hashtags: Optional[list] = None,
        location: Optional[str] = None
    ) -> Optional[Generation]:
        """Complete a generation with results."""
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return None
        
        generation.status = GenerationStatus.COMPLETED.value
        generation.image_url = image_url
        generation.caption = caption
        generation.hashtags = hashtags
        generation.location = location
        generation.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(generation)
        return generation
    
    @staticmethod
    def fail_generation(
        db: Session,
        generation_id: str,
        error_message: str,
        refund_credit: bool = True
    ) -> Optional[Generation]:
        """
        Mark generation as failed and optionally refund credit.
        """
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return None
        
        generation.status = GenerationStatus.FAILED.value
        generation.error_message = error_message
        generation.completed_at = datetime.utcnow()
        
        # Refund credit if requested
        if refund_credit:
            UserService.refund_credit(db, str(generation.user_id))
        
        db.commit()
        db.refresh(generation)
        return generation
    
    @staticmethod
    def get_user_generations(
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list[Generation]:
        """Get user's generation history."""
        return (
            db.query(Generation)
            .filter(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_generation_by_id(db: Session, generation_id: str) -> Optional[Generation]:
        """Get generation by ID."""
        return db.query(Generation).filter(Generation.id == generation_id).first()