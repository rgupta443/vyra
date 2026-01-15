"""
Analytics service for tracking user behavior and system metrics.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.analytics import AnalyticsEvent, EventType, SystemMetrics, ConversionMetrics
from app.models.user import User, PlanType
from app.models.generation import Generation, GenerationStatus


class AnalyticsService:
    """Service for tracking and analyzing system metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Event Tracking
    
    def track_event(
        self,
        event_type: EventType,
        user_id: Optional[UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> AnalyticsEvent:
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event to track
            user_id: Optional user ID associated with the event
            event_data: Optional additional event metadata
            duration_ms: Optional event duration in milliseconds
        
        Returns:
            Created analytics event
        """
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type.value,
            event_data=event_data,
            duration_ms=duration_ms
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def track_generation_request(self, user_id: UUID, generation_id: UUID, preset: str, format_type: str):
        """Track a generation request."""
        return self.track_event(
            event_type=EventType.GENERATION_REQUEST,
            user_id=user_id,
            event_data={
                "generation_id": str(generation_id),
                "preset": preset,
                "format": format_type
            }
        )
    
    def track_generation_success(self, user_id: UUID, generation_id: UUID, duration_ms: int):
        """Track a successful generation."""
        return self.track_event(
            event_type=EventType.GENERATION_SUCCESS,
            user_id=user_id,
            event_data={"generation_id": str(generation_id)},
            duration_ms=duration_ms
        )
    
    def track_generation_failure(self, user_id: UUID, generation_id: UUID, error: str):
        """Track a failed generation."""
        return self.track_event(
            event_type=EventType.GENERATION_FAILURE,
            user_id=user_id,
            event_data={
                "generation_id": str(generation_id),
                "error": error
            }
        )
    
    def track_plan_upgrade(self, user_id: UUID, from_plan: str, to_plan: str):
        """Track a plan upgrade and record conversion metrics."""
        # Track the event
        self.track_event(
            event_type=EventType.PLAN_UPGRADE,
            user_id=user_id,
            event_data={
                "from_plan": from_plan,
                "to_plan": to_plan
            }
        )
        
        # Record conversion metrics
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            generations_count = self.db.query(Generation).filter(
                Generation.user_id == user_id
            ).count()
            
            days_since_signup = (datetime.utcnow() - user.created_at).days
            
            conversion = ConversionMetrics(
                user_id=user_id,
                from_plan=from_plan,
                to_plan=to_plan,
                generations_before_conversion=generations_count,
                days_since_signup=days_since_signup
            )
            self.db.add(conversion)
            self.db.commit()
    
    def track_error(self, error_type: str, error_message: str, user_id: Optional[UUID] = None):
        """Track system or API errors."""
        event_type = EventType.API_ERROR if "api" in error_type.lower() else EventType.SYSTEM_ERROR
        return self.track_event(
            event_type=event_type,
            user_id=user_id,
            event_data={
                "error_type": error_type,
                "error_message": error_message
            }
        )
    
    # Usage Analytics
    
    def get_generations_per_user(self, user_id: UUID) -> int:
        """
        Get total number of generations for a user.
        Validates: Requirements 17.1
        """
        return self.db.query(Generation).filter(
            Generation.user_id == user_id
        ).count()
    
    def get_user_generation_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get detailed generation statistics for a user."""
        total = self.db.query(Generation).filter(
            Generation.user_id == user_id
        ).count()
        
        successful = self.db.query(Generation).filter(
            and_(
                Generation.user_id == user_id,
                Generation.status == GenerationStatus.COMPLETED.value
            )
        ).count()
        
        failed = self.db.query(Generation).filter(
            and_(
                Generation.user_id == user_id,
                Generation.status == GenerationStatus.FAILED.value
            )
        ).count()
        
        return {
            "total_generations": total,
            "successful_generations": successful,
            "failed_generations": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }
    
    # Conversion Analytics
    
    def get_conversion_rate(self, days: int = 30) -> float:
        """
        Calculate conversion rate from free to paid plans.
        Validates: Requirements 17.2
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total free users who signed up in the period
        total_free_users = self.db.query(User).filter(
            and_(
                User.created_at >= start_date,
                User.plan_type == PlanType.FREE.value
            )
        ).count()
        
        # Users who converted from free to paid
        conversions = self.db.query(ConversionMetrics).filter(
            and_(
                ConversionMetrics.converted_at >= start_date,
                ConversionMetrics.from_plan == PlanType.FREE.value,
                ConversionMetrics.to_plan.in_([PlanType.BASIC.value, PlanType.PRO.value])
            )
        ).count()
        
        # Current paid users who were free before
        current_paid = self.db.query(User).filter(
            and_(
                User.created_at >= start_date,
                User.plan_type.in_([PlanType.BASIC.value, PlanType.PRO.value])
            )
        ).count()
        
        total_eligible = total_free_users + current_paid
        
        if total_eligible == 0:
            return 0.0
        
        return (conversions / total_eligible) * 100
    
    def get_conversion_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed conversion metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conversions = self.db.query(ConversionMetrics).filter(
            ConversionMetrics.converted_at >= start_date
        ).all()
        
        if not conversions:
            return {
                "total_conversions": 0,
                "conversion_rate": 0.0,
                "avg_generations_before_conversion": 0,
                "avg_days_to_conversion": 0
            }
        
        avg_generations = sum(c.generations_before_conversion or 0 for c in conversions) / len(conversions)
        avg_days = sum(c.days_since_signup or 0 for c in conversions) / len(conversions)
        
        return {
            "total_conversions": len(conversions),
            "conversion_rate": self.get_conversion_rate(days),
            "avg_generations_before_conversion": round(avg_generations, 2),
            "avg_days_to_conversion": round(avg_days, 2)
        }
    
    # Error Rate Tracking
    
    def get_error_rate(self, hours: int = 24) -> float:
        """
        Calculate error rate for generations.
        Validates: Requirements 17.3
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        total_generations = self.db.query(Generation).filter(
            Generation.created_at >= start_time
        ).count()
        
        failed_generations = self.db.query(Generation).filter(
            and_(
                Generation.created_at >= start_time,
                Generation.status == GenerationStatus.FAILED.value
            )
        ).count()
        
        if total_generations == 0:
            return 0.0
        
        return (failed_generations / total_generations) * 100
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed error statistics."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Generation errors
        total_generations = self.db.query(Generation).filter(
            Generation.created_at >= start_time
        ).count()
        
        failed_generations = self.db.query(Generation).filter(
            and_(
                Generation.created_at >= start_time,
                Generation.status == GenerationStatus.FAILED.value
            )
        ).count()
        
        # System errors from events
        system_errors = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.created_at >= start_time,
                AnalyticsEvent.event_type.in_([
                    EventType.SYSTEM_ERROR.value,
                    EventType.API_ERROR.value
                ])
            )
        ).count()
        
        return {
            "total_generations": total_generations,
            "failed_generations": failed_generations,
            "error_rate": self.get_error_rate(hours),
            "system_errors": system_errors,
            "period_hours": hours
        }
    
    # System Metrics
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> SystemMetrics:
        """Record a system metric."""
        metric = SystemMetrics(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            tags=tags
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics.
        Validates: Requirements 17.1, 17.2, 17.3
        """
        # User metrics
        total_users = self.db.query(User).count()
        free_users = self.db.query(User).filter(User.plan_type == PlanType.FREE.value).count()
        paid_users = total_users - free_users
        
        # Generation metrics (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_generations = self.db.query(Generation).filter(
            Generation.created_at >= last_24h
        ).count()
        
        # Conversion metrics (last 30 days)
        conversion_rate = self.get_conversion_rate(days=30)
        
        # Error rate (last 24 hours)
        error_rate = self.get_error_rate(hours=24)
        
        return {
            "users": {
                "total": total_users,
                "free": free_users,
                "paid": paid_users
            },
            "generations": {
                "last_24h": recent_generations
            },
            "conversion": {
                "rate_30d": round(conversion_rate, 2)
            },
            "errors": {
                "rate_24h": round(error_rate, 2)
            }
        }
