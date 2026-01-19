"""
Redis configuration and connection management.

This module provides Redis connection and basic queue access.
For comprehensive queue management, use app.core.queue module.
"""
import redis
from rq import Queue

from app.core.config import settings

# Create Redis connection for general use (caching, sessions, etc.)
# This one decodes responses to strings for easier JSON handling
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Create separate Redis connection for RQ (job queue)
# RQ needs binary data for job serialization (pickle)
redis_queue_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=False,  # RQ needs binary data for job serialization
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Legacy queue instances for backward compatibility
# Use app.core.queue.QueueManager for new implementations
generation_queue = Queue("generation", connection=redis_queue_client)
processing_queue = Queue("processing", connection=redis_queue_client)


def get_redis():
    """Get Redis client instance for general use (caching, sessions)."""
    return redis_client


def get_redis_queue():
    """Get Redis client instance for RQ job queues."""
    return redis_queue_client


def get_generation_queue():
    """Get generation job queue (legacy - use QueueManager instead)."""
    return generation_queue


def get_processing_queue():
    """Get processing job queue (legacy - use QueueManager instead)."""
    return processing_queue