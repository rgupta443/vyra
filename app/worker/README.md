# Queue System Documentation

## Overview

The Instagram Content Automation queue system is built on Redis Queue (RQ) and provides a robust, scalable job processing infrastructure with automatic retry logic, error handling, and monitoring capabilities.

## Architecture

### Queue Types

The system uses four priority-based queues:

1. **High Priority Queue** (`high_priority`)
   - For critical operations (payments, urgent tasks)
   - Timeout: 10 minutes
   - Retry: 3 attempts with exponential backoff (10s, 30s, 60s)

2. **Generation Queue** (`generation`)
   - For image and caption generation tasks
   - Timeout: 15 minutes
   - Retry: 3 attempts with longer backoff (30s, 120s, 300s)

3. **Processing Queue** (`processing`)
   - For face processing and validation
   - Timeout: 5 minutes
   - Retry: 3 attempts with exponential backoff (10s, 30s, 60s)

4. **Analytics Queue** (`analytics`)
   - For analytics and tracking tasks
   - Timeout: 1 minute
   - Retry: 2 attempts with shorter backoff (5s, 15s)

### Job Types

The system supports five job types:

- `image_generation`: Generate Instagram-ready images
- `caption_generation`: Generate captions and hashtags
- `face_processing`: Process face embeddings
- `payment_processing`: Handle payment webhooks
- `analytics_tracking`: Track usage metrics

## Usage

### Enqueueing Jobs

#### Using Convenience Functions

```python
from app.core.queue import (
    enqueue_image_generation,
    enqueue_face_processing,
    enqueue_caption_generation
)

# Enqueue image generation
job = enqueue_image_generation(
    generation_id="gen_123",
    user_id="user_456",
    face_id="face_789",
    preset_type="luxury",
    format_type="reel_9_16"
)

# Enqueue face processing
job = enqueue_face_processing(
    face_id="face_789",
    image_path="/path/to/image.jpg"
)

# Enqueue caption generation
job = enqueue_caption_generation(
    generation_id="gen_123",
    image_url="https://example.com/image.jpg",
    preset_type="lifestyle"
)
```

#### Using Queue Manager Directly

```python
from app.core.queue import get_queue_manager, QueueName, JobType
from app.worker.tasks import generate_image_task

queue_manager = get_queue_manager()

job = queue_manager.enqueue_job(
    QueueName.GENERATION,
    JobType.IMAGE_GENERATION,
    generate_image_task,
    generation_id="gen_123",
    user_id="user_456",
    face_id="face_789",
    preset_type="luxury",
    format_type="reel_9_16"
)
```

### Monitoring Jobs

#### Get Job Status

```python
from app.core.queue import get_queue_manager

queue_manager = get_queue_manager()
status = queue_manager.get_job_status("job_id_here")

print(status)
# {
#     "job_id": "job_id_here",
#     "status": "finished",
#     "result": {...},
#     "meta": {...},
#     "created_at": "2024-01-01T00:00:00",
#     "started_at": "2024-01-01T00:00:01",
#     "ended_at": "2024-01-01T00:00:10"
# }
```

#### Get Queue Statistics

```python
from app.core.queue import get_queue_manager, QueueName

queue_manager = get_queue_manager()

# Get stats for a specific queue
stats = queue_manager.get_queue_stats(QueueName.GENERATION)

# Get stats for all queues
all_stats = queue_manager.get_all_queue_stats()
```

#### Health Check

```python
from app.core.queue import get_queue_manager

queue_manager = get_queue_manager()
health = queue_manager.health_check()

print(health)
# {
#     "status": "healthy",
#     "redis_connected": True,
#     "queues_initialized": 4,
#     "queue_stats": {...}
# }
```

### Cancelling Jobs

```python
from app.core.queue import get_queue_manager

queue_manager = get_queue_manager()
success = queue_manager.cancel_job("job_id_here")
```

## Running Workers

### Using Docker Compose

The default setup runs a worker that processes all queues:

```bash
docker-compose up worker
```

### Running Workers Manually

#### Process All Queues

```bash
python -m app.worker.worker
```

#### Process Specific Queues

```bash
# Generation tasks only
python -m app.worker.worker --type generation

# Processing tasks only
python -m app.worker.worker --type processing

# High priority tasks only
python -m app.worker.worker --type high-priority

# Analytics tasks only
python -m app.worker.worker --type analytics

# Custom queue selection
python -m app.worker.worker --queues generation processing
```

#### Custom Worker Name

```bash
python -m app.worker.worker --name my-custom-worker
```

## Error Handling

### Retry Logic

All jobs automatically retry on failure according to their queue configuration:

- **Automatic Retries**: Jobs retry up to 3 times (2 for analytics)
- **Exponential Backoff**: Retry delays increase with each attempt
- **Error Logging**: All failures are logged with full context

### Custom Error Types

Tasks can raise specific error types to control retry behavior:

```python
from app.worker.tasks import RetryableTaskError, NonRetryableTaskError

# Raise for temporary failures (will retry)
raise RetryableTaskError("API temporarily unavailable")

# Raise for permanent failures (won't retry)
raise NonRetryableTaskError("Invalid input parameters")
```

### Error Handling in Tasks

All tasks include comprehensive error handling:

```python
def my_task(param1, param2):
    try:
        # Task logic here
        result = do_something(param1, param2)
        return {"status": "completed", "result": result}
    
    except ValidationError as e:
        # Don't retry validation errors
        raise NonRetryableTaskError(f"Invalid parameters: {str(e)}")
    
    except APIError as e:
        # Retry API errors
        raise RetryableTaskError(f"API error: {str(e)}")
    
    except Exception as e:
        # Default: retry unexpected errors
        raise RetryableTaskError(f"Unexpected error: {str(e)}")
```

## API Endpoints

The queue system exposes monitoring endpoints:

### Health Check

```
GET /api/v1/queue/health
```

Returns queue system health status.

### Queue Statistics

```
GET /api/v1/queue/stats
GET /api/v1/queue/stats/{queue_name}
```

Returns statistics for all queues or a specific queue.

### Job Status

```
GET /api/v1/queue/job/{job_id}
```

Returns detailed status for a specific job.

### Cancel Job

```
DELETE /api/v1/queue/job/{job_id}
```

Cancels a pending job.

### List Queues

```
GET /api/v1/queue/queues
```

Lists all available queues with their configurations.

### List Job Types

```
GET /api/v1/queue/job-types
```

Lists all available job types.

## Requirements Validation

This queue system implementation satisfies the following requirements:

- **Requirement 16.1**: Automatic retry up to 3 times for failed operations
- **Requirement 16.2**: Clear, actionable error messages displayed to users
- **Requirement 16.3**: No silent failures - all errors logged and tracked
- **Requirement 16.4**: Credit refunds and failure logging when retries exhausted

## Testing

Run queue system tests:

```bash
# Run all queue tests
pytest tests/test_queue.py -v

# Run specific test classes
pytest tests/test_queue.py::TestQueueManager -v
pytest tests/test_queue.py::TestTaskErrorHandling -v

# Note: Some tests require Redis to be running
docker-compose up -d redis
pytest tests/test_queue.py -v
```

## Configuration

Queue configuration is managed in `app/core/queue.py`:

```python
class QueueConfig:
    QUEUE_CONFIGS = {
        QueueName.HIGH_PRIORITY: {
            "default_timeout": 600,
            "retry": Retry(max=3, interval=[10, 30, 60]),
            "job_timeout": 600,
        },
        # ... other queues
    }
```

Adjust timeouts and retry policies as needed for your use case.

## Best Practices

1. **Use Appropriate Queues**: Place jobs in the correct queue based on priority and type
2. **Set Realistic Timeouts**: Ensure job timeouts are appropriate for the task
3. **Handle Errors Properly**: Use RetryableTaskError and NonRetryableTaskError appropriately
4. **Monitor Queue Health**: Regularly check queue statistics and health endpoints
5. **Scale Workers**: Run multiple workers for high-throughput scenarios
6. **Log Comprehensively**: Include context in error logs for debugging

## Troubleshooting

### Jobs Not Processing

1. Check if workers are running: `docker-compose ps worker`
2. Check Redis connection: `docker-compose ps redis`
3. Check worker logs: `docker-compose logs worker`

### High Failure Rate

1. Check queue statistics: `GET /api/v1/queue/stats`
2. Review error logs in worker output
3. Verify external API availability (Nano Banana, OpenAI)
4. Check database connectivity

### Slow Processing

1. Monitor queue lengths: `GET /api/v1/queue/stats`
2. Scale workers: Run multiple worker instances
3. Optimize task implementations
4. Consider queue-specific workers for better parallelization
