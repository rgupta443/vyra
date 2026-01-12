"""
Face model definition for identity management.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Face(Base):
    """Face model for storing user face data and embeddings."""
    __tablename__ = "faces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    image_url = Column(String, nullable=False)
    embedding_data = Column(LargeBinary, nullable=False)  # Encrypted face embedding
    identity_strength = Column(Float, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="faces")
    generations = relationship("Generation", back_populates="face")