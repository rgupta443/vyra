"""
Health check and monitoring endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.monitoring_service import MonitoringService
from app.schemas.monitoring import (
    HealthCheckResponse,
    PerformanceMetricsResponse,
    AlertResponse
)

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive system health check endpoint.
    Returns health status of all system components.
    Validates: Requirements 17.4
    """
    monitoring_service = MonitoringService(db)
    health_status = monitoring_service.get_system_health()
    
    # Return appropriate status code based on health
    if health_status["status"] == "unhealthy":
        return health_status
    
    return health_status


@router.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    """Check database health."""
    monitoring_service = MonitoringService(db)
    return monitoring_service.check_database_health()


@router.get("/health/redis")
def redis_health(db: Session = Depends(get_db)):
    """Check Redis health."""
    monitoring_service = MonitoringService(db)
    return monitoring_service.check_redis_health()


@router.get("/health/queue")
def queue_health(db: Session = Depends(get_db)):
    """Check job queue health."""
    monitoring_service = MonitoringService(db)
    return monitoring_service.check_queue_health()


@router.get("/performance", response_model=PerformanceMetricsResponse)
def performance_metrics(db: Session = Depends(get_db)):
    """
    Get system performance metrics.
    Validates: Requirements 17.5
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_performance_metrics()


@router.get("/alerts", response_model=list[AlertResponse])
def get_recent_alerts(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent system alerts.
    Validates: Requirements 17.4
    """
    monitoring_service = MonitoringService(db)
    alerts = monitoring_service.get_recent_alerts(limit=limit)
    return alerts
