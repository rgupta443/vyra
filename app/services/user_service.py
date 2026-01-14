"""
User service for database operations and business logic.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.user import User, PlanType
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service class for user-related operations."""
    
    # Plan-based credit allocations
    PLAN_CREDITS = {
        PlanType.FREE: 5,
        PlanType.BASIC: 100,
        PlanType.PRO: 500
    }
    
    @staticmethod
    def create_user(db: Session, email: str, password: str) -> Optional[User]:
        """Create a new user with email and password."""
        try:
            hashed_password = get_password_hash(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                plan_type=PlanType.FREE.value,
                credits=UserService.PLAN_CREDITS[PlanType.FREE]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            return None  # User already exists
    
    @staticmethod
    def create_or_get_google_user(db: Session, email: str, google_id: str) -> User:
        """Create or get user from Google OAuth."""
        # Check if user exists with this Google ID
        user = db.query(User).filter(User.google_id == google_id).first()
        if user:
            return user
        
        # Check if user exists with this email
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link Google ID to existing user
            user.google_id = google_id
            db.commit()
            db.refresh(user)
            return user
        
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            plan_type=PlanType.FREE.value,
            credits=UserService.PLAN_CREDITS[PlanType.FREE]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def deduct_credit(db: Session, user_id: str) -> bool:
        """
        Deduct one credit from user's balance.
        Returns True if successful, False if insufficient credits.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if user.credits <= 0:
            return False
        
        user.credits -= 1
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return True
    
    @staticmethod
    def refund_credit(db: Session, user_id: str) -> bool:
        """
        Refund one credit to user's balance.
        Returns True if successful, False if user not found.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.credits += 1
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return True
    
    @staticmethod
    def has_credits(db: Session, user_id: str) -> bool:
        """Check if user has available credits."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.credits > 0
    
    @staticmethod
    def get_credit_balance(db: Session, user_id: str) -> int:
        """Get user's current credit balance."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.credits
    
    @staticmethod
    def update_plan(db: Session, user_id: str, new_plan: PlanType) -> Optional[User]:
        """
        Update user's plan and allocate credits based on new plan.
        Returns updated user or None if user not found.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update plan
        user.plan_type = new_plan.value
        
        # Allocate credits based on new plan
        user.credits = UserService.PLAN_CREDITS[new_plan]
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def add_credits(db: Session, user_id: str, amount: int) -> Optional[User]:
        """
        Add credits to user's balance.
        Returns updated user or None if user not found.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.credits += amount
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user