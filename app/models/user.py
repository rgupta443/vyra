"""
User model definition.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlanType(str, Enum):
    """User subscription plan types."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


class User(Base):
    """User model for authentication and account management."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    google_id = Column(String, unique=True, nullable=True)
    stripe_customer_id = Column(String, unique=True, nullable=True)  # Stripe customer ID
    
    plan_type = Column(String, default=PlanType.FREE.value)
    credits = Column(Integer, default=5)  # Free tier gets 5 credits
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    faces = relationship("Face", back_populates="user", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="user", cascade="all, delete-orphan")