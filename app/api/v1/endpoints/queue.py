"""
Queue management and monitoring endpoints.

This module provides API endpoints for monitoring and managing the job queue system
as required by the queue infrastructure setup.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.queue import get_queue_manager, QueueName, JobType
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class JobStatusResponse(BaseModel):
    """Response model for job status information."""
    job_id: str
    status: str
    result: Any = None
    meta: Dict[str, Any] = {}
    created_at: str = None
    started_at: str = None
    ended_at: str = None
    exc_info: str = None
    retry_count: int = None
    queue_name: str = None
    error: str = None


class QueueStatsResponse(BaseModel):
    """Response model for queue statistics."""
    queue_name: str
    length: int
    failed_job_count: int
    scheduled_job_count: int
    started_job_count: int
    deferred_job_count: int
    finished_job_count: int
    error: str = None


class HealthCheckResponse(BaseModel):
    """Response model for queue system health check."""
    status: str
    redis_connected: bool
    queues_initialized: int
    queue_stats: Dict[str, QueueStatsResponse]
    error: str = None


@router.get("/health", response_model=HealthCheckResponse)
async def queue_health_check():
    """
    Perform health check on the queue system.
    
    Returns comprehensive status of the queue infrastructure including
    Redis connectivity and queue statistics.
    """
    try:
        queue_manager = get_queue_manager()
        health_data = queue_manager.health_check()
        
        return HealthCheckResponse(**health_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Queue health check failed: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, QueueStatsResponse])
async def get_all_queue_stats(current_user: User = Depends(get_current_user)):
    """
    Get statistics for all queues.
    
    Requires authentication. Returns detailed statistics for monitoring
    queue performance and job processing status.
    """
    try:
        queue_manager = get_queue_manager()
        stats = queue_manager.get_all_queue_stats()
        
        return {
            queue_name: QueueStatsResponse(**queue_stats)
            for queue_name, queue_stats in stats.items()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue statistics: {str(e)}"
        )


@router.get("/stats/{queue_name}", response_model=QueueStatsResponse)
async def get_queue_stats(
    queue_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for a specific queue.
    
    Args:
        queue_name: Name of the queue to get stats for
        
    Returns:
        Queue statistics including job counts and status
    """
    try:
        # Validate queue name
        try:
            queue_enum = QueueName(queue_name)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid queue name: {queue_name}. Valid options: {[q.value for q in QueueName]}"
            )
        
        queue_manager = get_queue_manager()
        stats = queue_manager.get_queue_stats(queue_enum)
        
        return QueueStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue statistics: {str(e)}"
        )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status information for a specific job.
    
    Args:
        job_id: ID of the job to check
        
    Returns:
        Comprehensive job status information including results and metadata
    """
    try:
        queue_manager = get_queue_manager()
        status = queue_manager.get_job_status(job_id)
        
        return JobStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.delete("/job/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending job.
    
    Args:
        job_id: ID of the job to cancel
        
    Returns:
        Success status of the cancellation
    """
    try:
        queue_manager = get_queue_manager()
        success = queue_manager.cancel_job(job_id)
        
        if success:
            return {"message": f"Job {job_id} cancelled successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to cancel job {job_id}. Job may not exist or already be processed."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/queues", response_model=List[Dict[str, str]])
async def list_available_queues():
    """
    List all available queue names and their descriptions.
    
    Returns:
        List of queue information including names and descriptions
    """
    from app.core.queue import QueueConfig
    
    queues = []
    for queue_name, config in QueueConfig.QUEUE_CONFIGS.items():
        queues.append({
            "name": queue_name.value,
            "description": config["description"],
            "default_timeout": str(config["default_timeout"]),
            "max_retries": str(config["retry"].max)
        })
    
    return queues


@router.get("/job-types", response_model=List[str])
async def list_job_types():
    """
    List all available job types.
    
    Returns:
        List of job type names
    """
    return [job_type.value for job_type in JobType]