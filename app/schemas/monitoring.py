"""
Monitoring and health check schemas.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ComponentHealth(BaseModel):
    """Health status of a system component."""
    status: str
    message: str
    stuck_jobs: Optional[int] = None


class HealthCheckResponse(BaseModel):
    """System health check response."""
    status: str
    timestamp: str
    components: Dict[str, ComponentHealth]


class ErrorRateCheck(BaseModel):
    """Error rate check result."""
    alert: bool
    error_rate: float
    threshold: float
    message: Optional[str] = None


class LatencyCheck(BaseModel):
    """Latency check result."""
    alert: bool
    avg_latency_seconds: float
    threshold_seconds: int
    message: Optional[str] = None


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response."""
    error_rate: ErrorRateCheck
    latency: LatencyCheck
    timestamp: str


class AlertResponse(BaseModel):
    """Alert response."""
    level: str
    message: str
    data: Dict[str, Any]
    timestamp: str
