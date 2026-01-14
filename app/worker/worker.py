"""
RQ Worker script for processing background jobs.

This script starts RQ workers that process jobs from the configured queues
with proper error handling and retry logic as specified in requirements
16.1, 16.2, 16.3, and 16.4.
"""
import sys
import logging
from typing import List, Optional

from rq import Worker, Connection
from rq.exceptions import NoSuchJobError

from app.core.queue import get_queue_manager, QueueName
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CustomWorker(Worker):
    """Custom RQ Worker with enhanced error handling and logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logger
    
    def handle_exception(self, job, *exc_info):
        """Enhanced exception handling with detailed logging."""
        self.log.error(f"Job {job.id} failed with exception", exc_info=exc_info)
        
        # Log job context for debugging
        self.log.error(f"Failed job details: {job.meta}")
        
        # Call parent exception handler
        return super().handle_exception(job, *exc_info)
    
    def work(self, *args, **kwargs):
        """Override work method to add startup logging."""
        self.log.info(f"Worker {self.name} starting to process jobs from queues: {[q.name for q in self.queues]}")
        return super().work(*args, **kwargs)


def start_worker(queue_names: Optional[List[str]] = None, worker_name: Optional[str] = None):
    """
    Start an RQ worker to process jobs from specified queues.
    
    Args:
        queue_names: List of queue names to process. If None, processes all queues.
        worker_name: Custom name for the worker. If None, uses default naming.
    """
    try:
        queue_manager = get_queue_manager()
        
        # Determine which queues to process
        if queue_names:
            # Validate queue names
            valid_queue_names = [q.value for q in QueueName]
            invalid_queues = [q for q in queue_names if q not in valid_queue_names]
            if invalid_queues:
                raise ValueError(f"Invalid queue names: {invalid_queues}. Valid options: {valid_queue_names}")
            
            # Get specified queues
            queues = [queue_manager.get_queue(QueueName(name)) for name in queue_names]
        else:
            # Process all queues in priority order
            queues = [
                queue_manager.get_queue(QueueName.HIGH_PRIORITY),
                queue_manager.get_queue(QueueName.GENERATION),
                queue_manager.get_queue(QueueName.PROCESSING),
                queue_manager.get_queue(QueueName.ANALYTICS)
            ]
        
        logger.info(f"Starting worker for queues: {[q.name for q in queues]}")
        
        # Create and start worker
        with Connection(queue_manager.redis_client):
            worker = CustomWorker(
                queues,
                name=worker_name,
                connection=queue_manager.redis_client
            )
            
            # Start processing jobs
            worker.work(with_scheduler=True)
            
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}")
        sys.exit(1)


def start_generation_worker():
    """Start a worker specifically for generation tasks."""
    start_worker([QueueName.GENERATION.value], "generation-worker")


def start_processing_worker():
    """Start a worker specifically for processing tasks."""
    start_worker([QueueName.PROCESSING.value], "processing-worker")


def start_high_priority_worker():
    """Start a worker specifically for high priority tasks."""
    start_worker([QueueName.HIGH_PRIORITY.value], "high-priority-worker")


def start_analytics_worker():
    """Start a worker specifically for analytics tasks."""
    start_worker([QueueName.ANALYTICS.value], "analytics-worker")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start RQ worker for Instagram Content Automation")
    parser.add_argument(
        "--queues",
        nargs="*",
        help=f"Queue names to process. Options: {[q.value for q in QueueName]}",
        default=None
    )
    parser.add_argument(
        "--name",
        help="Custom worker name",
        default=None
    )
    parser.add_argument(
        "--type",
        choices=["generation", "processing", "high-priority", "analytics", "all"],
        help="Predefined worker type",
        default="all"
    )
    
    args = parser.parse_args()
    
    if args.type == "generation":
        start_generation_worker()
    elif args.type == "processing":
        start_processing_worker()
    elif args.type == "high-priority":
        start_high_priority_worker()
    elif args.type == "analytics":
        start_analytics_worker()
    else:
        start_worker(args.queues, args.name)