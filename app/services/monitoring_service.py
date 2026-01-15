"""
Monitoring and alerting service for system health and critical errors.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.generation import Generation, GenerationStatus
from app.models.analytics import AnalyticsEvent, EventType, SystemMetrics
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringService:
    """Service for system monitoring and alerting."""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis()
    
    # Health Checks
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        Check database connectivity and health.
        Validates: Requirements 17.4
        """
        try:
            # Simple query to test database connection
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
    
    def check_redis_health(self) -> Dict[str, Any]:
        """
        Check Redis connectivity and health.
        Validates: Requirements 17.4
        """
        try:
            self.redis.ping()
            return {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}"
            }
    
    def check_queue_health(self) -> Dict[str, Any]:
        """
        Check job queue health and pending jobs.
        Validates: Requirements 17.4
        """
        try:
            # Check for stuck jobs (pending for more than 1 hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            stuck_jobs = self.db.query(Generation).filter(
                and_(
                    Generation.status.in_([
                        GenerationStatus.PENDING.value,
                        GenerationStatus.PROCESSING.value
                    ]),
                    Generation.created_at < one_hour_ago
                )
            ).count()
            
            if stuck_jobs > 10:
                return {
                    "status": "degraded",
                    "message": f"Found {stuck_jobs} stuck jobs",
                    "stuck_jobs": stuck_jobs
                }
            
            return {
                "status": "healthy",
                "message": "Queue processing normally",
                "stuck_jobs": stuck_jobs
            }
        except Exception as e:
            logger.error(f"Queue health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Queue health check failed: {str(e)}"
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        Validates: Requirements 17.4
        """
        db_health = self.check_database_health()
        redis_health = self.check_redis_health()
        queue_health = self.check_queue_health()
        
        # Determine overall status
        statuses = [db_health["status"], redis_health["status"], queue_health["status"]]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_health,
                "redis": redis_health,
                "queue": queue_health
            }
        }
    
    # Performance Monitoring
    
    def check_error_rate_threshold(self, threshold: float = 10.0, hours: int = 1) -> Dict[str, Any]:
        """
        Check if error rate exceeds threshold.
        Validates: Requirements 17.4, 17.5
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        total_generations = self.db.query(Generation).filter(
            Generation.created_at >= start_time
        ).count()
        
        if total_generations == 0:
            return {
                "alert": False,
                "error_rate": 0.0,
                "threshold": threshold
            }
        
        failed_generations = self.db.query(Generation).filter(
            and_(
                Generation.created_at >= start_time,
                Generation.status == GenerationStatus.FAILED.value
            )
        ).count()
        
        error_rate = (failed_generations / total_generations) * 100
        
        if error_rate > threshold:
            alert_message = f"Error rate {error_rate:.2f}% exceeds threshold {threshold}%"
            logger.error(alert_message)
            self._send_alert(
                level=AlertLevel.ERROR,
                message=alert_message,
                data={
                    "error_rate": error_rate,
                    "threshold": threshold,
                    "failed_generations": failed_generations,
                    "total_generations": total_generations
                }
            )
            return {
                "alert": True,
                "error_rate": error_rate,
                "threshold": threshold,
                "message": alert_message
            }
        
        return {
            "alert": False,
            "error_rate": error_rate,
            "threshold": threshold
        }
    
    def check_generation_latency(self, threshold_seconds: int = 300) -> Dict[str, Any]:
        """
        Check average generation latency.
        Validates: Requirements 17.5
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        completed_generations = self.db.query(Generation).filter(
            and_(
                Generation.created_at >= one_hour_ago,
                Generation.status == GenerationStatus.COMPLETED.value,
                Generation.completed_at.isnot(None)
            )
        ).all()
        
        if not completed_generations:
            return {
                "alert": False,
                "avg_latency_seconds": 0,
                "threshold_seconds": threshold_seconds
            }
        
        latencies = [
            (gen.completed_at - gen.created_at).total_seconds()
            for gen in completed_generations
        ]
        avg_latency = sum(latencies) / len(latencies)
        
        if avg_latency > threshold_seconds:
            alert_message = f"Average generation latency {avg_latency:.2f}s exceeds threshold {threshold_seconds}s"
            logger.warning(alert_message)
            self._send_alert(
                level=AlertLevel.WARNING,
                message=alert_message,
                data={
                    "avg_latency_seconds": avg_latency,
                    "threshold_seconds": threshold_seconds,
                    "sample_size": len(latencies)
                }
            )
            return {
                "alert": True,
                "avg_latency_seconds": avg_latency,
                "threshold_seconds": threshold_seconds,
                "message": alert_message
            }
        
        return {
            "alert": False,
            "avg_latency_seconds": avg_latency,
            "threshold_seconds": threshold_seconds
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics.
        Validates: Requirements 17.5
        """
        error_rate_check = self.check_error_rate_threshold()
        latency_check = self.check_generation_latency()
        
        return {
            "error_rate": error_rate_check,
            "latency": latency_check,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Alerting
    
    def _send_alert(
        self,
        level: AlertLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Send an alert (log for now, can be extended to email/Slack/PagerDuty).
        Validates: Requirements 17.4
        """
        alert_data = {
            "level": level.value,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the alert
        if level == AlertLevel.CRITICAL:
            logger.critical(f"CRITICAL ALERT: {message}", extra=alert_data)
        elif level == AlertLevel.ERROR:
            logger.error(f"ERROR ALERT: {message}", extra=alert_data)
        elif level == AlertLevel.WARNING:
            logger.warning(f"WARNING ALERT: {message}", extra=alert_data)
        else:
            logger.info(f"INFO ALERT: {message}", extra=alert_data)
        
        # Store alert in Redis for dashboard display
        try:
            alert_key = f"alert:{datetime.utcnow().timestamp()}"
            self.redis.setex(
                alert_key,
                3600,  # Keep alerts for 1 hour
                str(alert_data)
            )
        except Exception as e:
            logger.error(f"Failed to store alert in Redis: {str(e)}")
    
    def alert_critical_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """
        Send a critical error alert.
        Validates: Requirements 17.4
        """
        self._send_alert(
            level=AlertLevel.CRITICAL,
            message=f"Critical error: {error_type} - {error_message}",
            data={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
        
        # Track in analytics
        event = AnalyticsEvent(
            event_type=EventType.SYSTEM_ERROR.value,
            event_data={
                "error_type": error_type,
                "error_message": error_message,
                "severity": "critical",
                "context": context or {}
            }
        )
        self.db.add(event)
        self.db.commit()
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts from Redis."""
        try:
            # Get all alert keys
            alert_keys = self.redis.keys("alert:*")
            
            # Sort by timestamp (descending)
            alert_keys.sort(reverse=True)
            
            # Get the most recent alerts
            alerts = []
            for key in alert_keys[:limit]:
                alert_data = self.redis.get(key)
                if alert_data:
                    alerts.append(eval(alert_data))  # Note: In production, use json.loads
            
            return alerts
        except Exception as e:
            logger.error(f"Failed to retrieve alerts from Redis: {str(e)}")
            return []
