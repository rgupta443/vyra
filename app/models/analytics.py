"""
Analytics model for tracking system metrics and user behavior.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, Enum):
    """Analytics event types."""
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    FACE_UPLOAD = "face_upload"
    GENERATION_REQUEST = "generation_request"
    GENERATION_SUCCESS = "generation_success"
    GENERATION_FAILURE = "generation_failure"
    PLAN_UPGRADE = "plan_upgrade"
    PLAN_DOWNGRADE = "plan_downgrade"
    CREDIT_PURCHASE = "credit_purchase"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"
    API_ERROR = "api_error"
    SYSTEM_ERROR = "system_error"


class AnalyticsEvent(Base):
    """Analytics event tracking for user actions and system events."""
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Nullable for system events
    
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(JSON, nullable=True)  # Additional event metadata
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Event duration in milliseconds
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class SystemMetrics(Base):
    """Aggregated system metrics for monitoring and alerting."""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)  # e.g., "count", "percentage", "ms"
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Additional metric tags
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ConversionMetrics(Base):
    """Conversion tracking for free to paid plan upgrades."""
    __tablename__ = "conversion_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    from_plan = Column(String, nullable=False)
    to_plan = Column(String, nullable=False)
    
    # Conversion context
    generations_before_conversion = Column(Integer, nullable=True)
    days_since_signup = Column(Integer, nullable=True)
    
    converted_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
