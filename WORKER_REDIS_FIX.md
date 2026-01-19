# Worker Redis Decode Error Fix

## Issue 1: Redis Decode Error
Worker was crashing with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x9c in position 1: invalid start byte` when trying to process queued jobs.

### Root Cause
The Redis client was configured with `decode_responses=True`, which automatically decodes all Redis responses from bytes to UTF-8 strings. However, RQ (Redis Queue) stores job data as pickled Python objects, which are binary data and cannot be decoded as UTF-8 strings.

### Solution
Created **two separate Redis clients**:

1. **General Redis Client** (`redis_client`) - with `decode_responses=True`
   - Used for: caching, sessions, simple key-value storage
   - Returns: strings (automatically decoded from bytes)
   - Used by: `SessionService`, `CacheService`, `PerformanceMonitor`, etc.

2. **Queue Redis Client** (`redis_queue_client`) - with `decode_responses=False`
   - Used for: RQ job queues
   - Returns: bytes (raw binary data for pickle deserialization)
   - Used by: `QueueManager`, RQ workers

## Issue 2: Event Loop Closed Error
Worker was crashing with `RuntimeError: Event loop is closed` when trying to run async operations.

### Root Cause
The task code was calling `asyncio.run()` multiple times:
1. Once for the main async operation (e.g., `generate_image()`)
2. Once for cleanup (e.g., `nano_service.close()`)

The problem is that `asyncio.run()` creates a new event loop, runs the coroutine, and then **closes the loop**. When you try to call it again, the loop is already closed.

### Solution
Wrapped all async operations in a single async function and called `asyncio.run()` only once:

```python
# Before (BROKEN):
image_url = asyncio.run(nano_service.generate_image(...))
asyncio.run(nano_service.close())  # ERROR: Event loop is closed!

# After (FIXED):
async def run_generation():
    try:
        image_url = await nano_service.generate_image(...)
        return image_url
    finally:
        await nano_service.close()

image_url = asyncio.run(run_generation())  # Single event loop for all operations
```

## Files Modified

### 1. `app/core/redis.py`
- Added `redis_queue_client` for RQ operations
- Kept `redis_client` for general operations
- Updated legacy queue instances to use `redis_queue_client`
- Added `get_redis_queue()` function

### 2. `app/core/queue.py`
- Updated `QueueManager.__init__()` to use `decode_responses=False`
- Added comment explaining why binary data is needed

### 3. `app/worker/tasks.py`
- Fixed `generate_image_task()` to use single event loop
- Fixed `generate_caption_task()` to use single event loop
- Wrapped all async operations in async wrapper functions
- Ensured cleanup happens in the same event loop

## Testing
After these fixes, the worker should start successfully and process jobs:

```bash
python -m app.worker.worker
```

Expected output:
```
INFO - Worker starting to process jobs from queues: ['high_priority', 'generation', 'processing', 'analytics']
INFO - Starting image generation task for generation <id>
INFO - Image generation successful for generation <id>
INFO - Queued caption generation job for generation <id>
INFO - Starting caption generation for generation <id>
INFO - Caption generated for <id>
INFO - Caption generation task completed for generation <id>
```

## Why This Works

### Redis Fix
- RQ uses Python's `pickle` module to serialize job functions and arguments
- Pickle produces binary data that is NOT valid UTF-8
- When Redis tries to decode this binary data as UTF-8, it fails
- By keeping the data as bytes, RQ can properly unpickle the job data

### Event Loop Fix
- `asyncio.run()` is designed for top-level entry points
- It creates a new event loop, runs the coroutine, and closes the loop
- Calling it multiple times causes "Event loop is closed" errors
- By wrapping all async operations in one function, we use a single event loop
- The `finally` block ensures cleanup happens in the same loop before it closes

## Related
- Issue: Worker crash on startup when jobs are queued
- Status: Fixed
- Date: 2026-01-20
