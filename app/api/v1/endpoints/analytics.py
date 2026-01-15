"""
Analytics API endpoints for tracking and monitoring.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    DashboardMetricsResponse,
    UserStatsResponse,
    ConversionMetricsResponse,
    ErrorStatsResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard metrics.
    Requires authentication.
    """
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_dashboard_metrics()
    return metrics


@router.get("/user/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get generation statistics for the current user.
    """
    analytics_service = AnalyticsService(db)
    stats = analytics_service.get_user_generation_stats(current_user.id)
    return stats


@router.get("/conversions", response_model=ConversionMetricsResponse)
def get_conversion_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get conversion metrics for the specified period.
    Requires authentication.
    """
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_conversion_metrics(days=days)
    return metrics


@router.get("/errors", response_model=ErrorStatsResponse)
def get_error_stats(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get error statistics for the specified period.
    Requires authentication.
    """
    analytics_service = AnalyticsService(db)
    stats = analytics_service.get_error_stats(hours=hours)
    return stats
