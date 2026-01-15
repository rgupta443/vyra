"""
Analytics schemas for API responses.
"""
from typing import Dict, Any
from pydantic import BaseModel


class UserMetrics(BaseModel):
    """User count metrics."""
    total: int
    free: int
    paid: int


class GenerationMetrics(BaseModel):
    """Generation count metrics."""
    last_24h: int


class ConversionMetrics(BaseModel):
    """Conversion rate metrics."""
    rate_30d: float


class ErrorMetrics(BaseModel):
    """Error rate metrics."""
    rate_24h: float


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response."""
    users: UserMetrics
    generations: GenerationMetrics
    conversion: ConversionMetrics
    errors: ErrorMetrics


class UserStatsResponse(BaseModel):
    """User generation statistics response."""
    total_generations: int
    successful_generations: int
    failed_generations: int
    success_rate: float


class ConversionMetricsResponse(BaseModel):
    """Conversion metrics response."""
    total_conversions: int
    conversion_rate: float
    avg_generations_before_conversion: float
    avg_days_to_conversion: float


class ErrorStatsResponse(BaseModel):
    """Error statistics response."""
    total_generations: int
    failed_generations: int
    error_rate: float
    system_errors: int
    period_hours: int
