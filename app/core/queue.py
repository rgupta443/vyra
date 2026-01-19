"""
Queue system configuration and management for Instagram Content Automation.

This module provides a comprehensive job queue system using Redis Queue (RQ)
with proper retry logic, error handling, and job type management as specified
in requirements 16.1, 16.2, 16.3, and 16.4.
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import timedelta

import redis
from rq import Queue, Worker, Connection, Retry
from rq.job import Job
from rq.exceptions import NoSuchJobError

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobType(str, Enum):
    """Enumeration of job types for different operations."""
    IMAGE_GENERATION = "image_generation"
    CAPTION_GENERATION = "caption_generation" 
    FACE_PROCESSING = "face_processing"
    PAYMENT_PROCESSING = "payment_processing"
    ANALYTICS_TRACKING = "analytics_tracking"


class QueueName(str, Enum):
    """Enumeration of queue names for different priorities."""
    HIGH_PRIORITY = "high_priority"
    GENERATION = "generation"
    PROCESSING = "processing"
    ANALYTICS = "analytics"


class QueueConfig:
    """Configuration for different queue types with retry policies."""
    
    QUEUE_CONFIGS = {
        QueueName.HIGH_PRIORITY: {
            "default_timeout": 600,  # 10 minutes
            "retry": Retry(max=3, interval=[10, 30, 60]),  # Exponential backoff
            "job_timeout": 600,
            "description": "High priority jobs (payments, critical operations)"
        },
        QueueName.GENERATION: {
            "default_timeout": 900,  # 15 minutes
            "retry": Retry(max=3, interval=[30, 120, 300]),  # Longer backoff for AI operations
            "job_timeout": 900,
            "description": "Image and content generation jobs"
        },
        QueueName.PROCESSING: {
            "default_timeout": 300,  # 5 minutes
            "retry": Retry(max=3, interval=[10, 30, 60]),
            "job_timeout": 300,
            "description": "Face processing and validation jobs"
        },
        QueueName.ANALYTICS: {
            "default_timeout": 60,  # 1 minute
            "retry": Retry(max=2, interval=[5, 15]),  # Fewer retries for analytics
            "job_timeout": 60,
            "description": "Analytics and tracking jobs"
        }
    }


class QueueManager:
    """Centralized queue management system."""
    
    def __init__(self):
        """Initialize queue manager with Redis connection."""
        # Use separate Redis client for RQ that doesn't decode responses
        # RQ stores pickled Python objects which are binary data
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # RQ needs binary data for job serialization
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        self._queues: Dict[QueueName, Queue] = {}
        self._initialize_queues()
    
    def _initialize_queues(self) -> None:
        """Initialize all queues with their configurations."""
        for queue_name, config in QueueConfig.QUEUE_CONFIGS.items():
            self._queues[queue_name] = Queue(
                name=queue_name.value,
                connection=self.redis_client,
                default_timeout=config["default_timeout"]
            )
            logger.info(f"Initialized queue: {queue_name.value} - {config['description']}")
    
    def get_queue(self, queue_name: QueueName) -> Queue:
        """Get a specific queue by name."""
        return self._queues[queue_name]
    
    def enqueue_job(
        self,
        queue_name: QueueName,
        job_type: JobType,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        **kwargs
    ) -> Job:
        """
        Enqueue a job with proper retry configuration and error handling.
        
        Args:
            queue_name: Target queue for the job
            job_type: Type of job being enqueued
            func: Function to execute
            *args: Function arguments
            job_id: Optional custom job ID
            **kwargs: Function keyword arguments
            
        Returns:
            RQ Job instance
            
        Raises:
            Exception: If job enqueueing fails
        """
        try:
            queue = self.get_queue(queue_name)
            config = QueueConfig.QUEUE_CONFIGS[queue_name]
            
            # Add job metadata
            job_kwargs = {
                "retry": config["retry"],
                "job_timeout": config["job_timeout"],
                "meta": {
                    "job_type": job_type.value,
                    "queue_name": queue_name.value,
                    "enqueued_at": str(timedelta(seconds=0))  # Will be set by RQ
                }
            }
            
            if job_id:
                job_kwargs["job_id"] = job_id
            
            job = queue.enqueue(func, *args, **job_kwargs, **kwargs)
            
            logger.info(
                f"Enqueued job {job.id} of type {job_type.value} to queue {queue_name.value}"
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to enqueue job of type {job_type.value}: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get comprehensive job status information.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dictionary with job status information
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_client)
            
            return {
                "job_id": job.id,
                "status": job.get_status(),
                "result": job.result,
                "meta": job.meta,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "exc_info": job.exc_info,
                "retry_count": getattr(job, 'retries_left', None),
                "queue_name": job.origin
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": str(e)
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job if it's still pending.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_client)
            job.cancel()
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False
    
    def get_queue_stats(self, queue_name: QueueName) -> Dict[str, Any]:
        """
        Get statistics for a specific queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Dictionary with queue statistics
        """
        try:
            queue = self.get_queue(queue_name)
            
            return {
                "queue_name": queue_name.value,
                "length": len(queue),
                "failed_job_count": queue.failed_job_registry.count,
                "scheduled_job_count": queue.scheduled_job_registry.count,
                "started_job_count": queue.started_job_registry.count,
                "deferred_job_count": queue.deferred_job_registry.count,
                "finished_job_count": queue.finished_job_registry.count
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for queue {queue_name.value}: {str(e)}")
            return {"error": str(e)}
    
    def get_all_queue_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all queues."""
        stats = {}
        for queue_name in QueueName:
            stats[queue_name.value] = self.get_queue_stats(queue_name)
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the queue system.
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Test Redis connection
            self.redis_client.ping()
            
            # Get basic stats
            stats = self.get_all_queue_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "queues_initialized": len(self._queues),
                "queue_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Queue system health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e)
            }


# Global queue manager instance
queue_manager = QueueManager()


def get_queue_manager() -> QueueManager:
    """Get the global queue manager instance."""
    return queue_manager


def get_redis_connection():
    """Get Redis connection for direct access if needed."""
    return queue_manager.redis_client


# Convenience functions for common operations
def enqueue_image_generation(generation_id: str, user_id: str, face_id: str, 
                           preset_type: str, format_type: str) -> Job:
    """Enqueue an image generation job."""
    from app.worker.tasks import generate_image_task
    
    return queue_manager.enqueue_job(
        QueueName.GENERATION,
        JobType.IMAGE_GENERATION,
        generate_image_task,
        generation_id=generation_id,
        user_id=user_id,
        face_id=face_id,
        preset_type=preset_type,
        format_type=format_type,
        job_id=f"img_gen_{generation_id}"
    )


def enqueue_face_processing(face_id: str, image_path: str) -> Job:
    """Enqueue a face processing job."""
    from app.worker.tasks import process_face_embedding_task
    
    return queue_manager.enqueue_job(
        QueueName.PROCESSING,
        JobType.FACE_PROCESSING,
        process_face_embedding_task,
        face_id=face_id,
        image_path=image_path,
        job_id=f"face_proc_{face_id}"
    )


def enqueue_caption_generation(generation_id: str, image_url: str, preset_type: str) -> Job:
    """Enqueue a caption generation job."""
    from app.worker.tasks import generate_caption_task
    
    return queue_manager.enqueue_job(
        QueueName.GENERATION,
        JobType.CAPTION_GENERATION,
        generate_caption_task,
        generation_id=generation_id,
        image_url=image_url,
        preset_type=preset_type,
        job_id=f"caption_gen_{generation_id}"
    )


def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics for all queues.
    
    Returns:
        Dict with queue statistics
    """
    try:
        redis_conn = get_redis_connection()
        stats = {}
        
        # Use QueueName enum values
        for queue_name in [q.value for q in QueueName]:
            queue = Queue(queue_name, connection=redis_conn)
            stats[queue_name] = {
                "count": len(queue),
                "started_jobs": queue.started_job_registry.count,
                "finished_jobs": queue.finished_job_registry.count,
                "failed_jobs": queue.failed_job_registry.count,
                "deferred_jobs": queue.deferred_job_registry.count,
            }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {}
