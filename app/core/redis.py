"""
Redis configuration and connection management.
"""
import redis
from rq import Queue

from app.core.config import settings

# Create Redis connection
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Create job queues
generation_queue = Queue("generation", connection=redis_client)
processing_queue = Queue("processing", connection=redis_client)


def get_redis():
    """Get Redis client instance."""
    return redis_client


def get_generation_queue():
    """Get generation job queue."""
    return generation_queue


def get_processing_queue():
    """Get processing job queue."""
    return processing_queue