# Performance Optimization Guide

## Overview

This document describes the performance optimizations implemented in the Instagram Content Automation system, including caching strategies, database query optimization, and resource management.

## Caching Strategy

### Redis-Based Caching

The system uses Redis for caching frequently accessed data to reduce database load and improve response times.

#### Cache Service (`app/services/cache_service.py`)

**Cached Data Types:**

1. **User Data** (TTL: 10 minutes)
   - User profile information
   - Plan type and status
   - Reduces database queries for authentication

2. **Face Data** (TTL: 30 minutes)
   - Face embeddings
   - Face metadata
   - Long TTL because faces rarely change

3. **Generation Data** (TTL: 1 minute)
   - Generation status
   - Short TTL for real-time updates
   - Invalidated on status changes

4. **Preset Data** (TTL: 1 hour)
   - Preset configurations
   - Long TTL because presets rarely change
   - Invalidated when presets are updated

5. **Credit Balance** (TTL: 30 seconds)
   - User credit balance
   - Short TTL for accuracy
   - Invalidated on credit changes

**Cache Invalidation:**

- Automatic expiration based on TTL
- Manual invalidation on data updates
- Pattern-based invalidation for bulk operations

**Usage Example:**

```python
from app.services.cache_service import CacheService

# Get cached user data
user_data = CacheService.get_user(user_id)
if not user_data:
    # Cache miss - fetch from database
    user_data = fetch_from_db(user_id)
    CacheService.set_user(user_id, user_data)

# Invalidate cache on update
CacheService.invalidate_user(user_id)
```

**Decorator-Based Caching:**

```python
from app.services.cache_service import cached

@cached("user_profile:", ttl=600)
def get_user_profile(user_id: str):
    # Expensive database query
    return db.query(User).filter(User.id == user_id).first()
```

### Cache Hit Rate Monitoring

The system tracks cache hit rates to measure caching effectiveness:

- Target hit rate: >80%
- Monitored via performance monitoring service
- Alerts if hit rate drops below threshold

## Database Query Optimization

### Query Optimizer Service (`app/services/query_optimizer.py`)

**Optimization Techniques:**

1. **Eager Loading**
   - Prevents N+1 query problem
   - Uses `joinedload()` for one-to-one relations
   - Uses `selectinload()` for one-to-many relations

2. **Batch Operations**
   - Bulk insert/update for multiple records
   - Reduces round trips to database
   - Improves throughput for large datasets

3. **Selective Loading**
   - Load only required fields
   - Reduces memory usage
   - Faster query execution

4. **Existence Checks**
   - Use `exists()` instead of loading full records
   - More efficient for boolean checks
   - Reduces data transfer

**Example: Optimized User Query**

```python
# Bad: N+1 query problem
user = db.query(User).filter(User.id == user_id).first()
face = db.query(Face).filter(Face.user_id == user.id).first()

# Good: Single query with eager loading
user = QueryOptimizer.get_user_with_face(db, user_id)
face = user.faces[0] if user.faces else None
```

**Example: Batch Operations**

```python
# Bad: Multiple individual inserts
for record in records:
    db.add(Model(**record))
    db.commit()

# Good: Bulk insert
BatchOperations.bulk_insert(db, Model, records)
```

### Database Indexes

**Recommended Indexes:**

1. **Users Table**
   - `idx_user_email` - For login queries
   - `idx_user_google_id` - For OAuth queries

2. **Faces Table**
   - `idx_face_user_id` - For user face queries
   - `idx_face_user_id_active` - Composite for active face queries

3. **Generations Table**
   - `idx_generation_user_id` - For user generation queries
   - `idx_generation_status` - For status filtering
   - `idx_generation_user_id_status` - Composite index
   - `idx_generation_created_at` - For date ordering
   - `idx_generation_user_id_created_at` - Composite for user + date

4. **Presets Table**
   - `idx_preset_name` - For preset lookup
   - `idx_preset_is_active` - For active preset queries

**Index Usage Guidelines:**

- Use composite indexes for frequently combined filters
- Keep indexes on foreign keys
- Monitor index usage with query profiling
- Remove unused indexes to reduce write overhead

### Connection Pooling

**Configuration:**

```python
# SQLAlchemy connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Number of connections to maintain
    max_overflow=10,  # Additional connections when pool is full
    pool_timeout=30,  # Timeout for getting connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
)
```

**Benefits:**

- Reuses database connections
- Reduces connection overhead
- Handles connection failures gracefully
- Scales with concurrent requests

## Performance Monitoring

### Performance Monitor Service (`app/services/performance_monitor.py`)

**Monitored Metrics:**

1. **Request Timing**
   - Average response time per endpoint
   - 95th percentile response time
   - Slow request identification

2. **Database Query Timing**
   - Query execution time by type
   - Slow query identification
   - Query count per request

3. **Cache Performance**
   - Cache hit rate
   - Cache miss rate
   - Cache operation timing

4. **System Resources**
   - CPU usage
   - Memory usage
   - Thread count
   - Open file descriptors

**Usage Example:**

```python
from app.services.performance_monitor import measure_time, timed

# Context manager for timing
with measure_time("expensive_operation"):
    result = expensive_operation()

# Decorator for timing
@timed("database_query")
def fetch_data():
    return db.query(Model).all()
```

**Performance Summary Endpoint:**

```
GET /api/v1/monitoring/performance
```

Returns:
```json
{
  "cache_hit_rate": 85.5,
  "system_metrics": {
    "cpu_percent": 15.2,
    "memory_mb": 256.8,
    "memory_percent": 12.5,
    "threads": 10,
    "open_files": 25
  }
}
```

## Image Processing Optimization

### Face Embedding Caching

**Strategy:**

1. Generate face embedding once on upload
2. Encrypt and store in database
3. Cache in Redis for fast access
4. Reuse across all generations

**Benefits:**

- Eliminates redundant face processing
- Reduces API calls to face detection service
- Faster generation start time
- Lower costs

### Image Format Optimization

**Techniques:**

1. **Lazy Loading**
   - Load images only when needed
   - Reduces initial page load time

2. **Progressive Loading**
   - Show low-quality preview first
   - Load high-quality version in background

3. **CDN Integration**
   - Serve images from CDN
   - Reduces server load
   - Faster delivery to users

## Queue System Optimization

### Job Prioritization

**Priority Levels:**

1. **High Priority** (10)
   - Payment processing
   - Credit allocation
   - User-facing operations

2. **Normal Priority** (5)
   - Image generation
   - Caption generation

3. **Low Priority** (1)
   - Analytics tracking
   - Background cleanup

### Worker Scaling

**Configuration:**

```python
# Number of workers per queue
IMAGE_GENERATION_WORKERS = 4
CAPTION_GENERATION_WORKERS = 2
ANALYTICS_WORKERS = 1
```

**Scaling Strategy:**

- Scale workers based on queue depth
- Monitor job processing time
- Add workers during peak hours
- Reduce workers during off-peak

### Job Batching

**Techniques:**

1. **Batch Analytics Events**
   - Collect multiple events
   - Process in single batch
   - Reduces database writes

2. **Batch Notifications**
   - Group notifications by user
   - Send in single request
   - Reduces API calls

## API Response Optimization

### Pagination

**Implementation:**

```python
@router.get("/generations")
def get_generations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    generations = (
        db.query(Generation)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return generations
```

**Benefits:**

- Reduces response size
- Faster response times
- Lower memory usage
- Better user experience

### Response Compression

**Configuration:**

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Benefits:**

- Reduces bandwidth usage
- Faster response delivery
- Lower costs

### Field Selection

**Implementation:**

```python
@router.get("/user")
def get_user(
    fields: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    
    if fields:
        # Load only requested fields
        field_list = fields.split(",")
        query = query.options(load_only(*field_list))
    
    return query.first()
```

**Benefits:**

- Reduces response size
- Faster serialization
- Lower bandwidth usage

## Frontend Performance

### Code Splitting

**Implementation:**

```typescript
// Lazy load components
const GeneratePage = dynamic(() => import('./generate/page'))
const ResultsPage = dynamic(() => import('./results/[jobId]/page'))
```

**Benefits:**

- Smaller initial bundle size
- Faster page load
- Better user experience

### Request Deduplication

**Implementation:**

```typescript
// React Query automatically deduplicates requests
const { data } = useQuery(['user', userId], fetchUser)
```

**Benefits:**

- Reduces redundant API calls
- Lower server load
- Faster response times

### Optimistic Updates

**Implementation:**

```typescript
const mutation = useMutation(updateUser, {
  onMutate: async (newData) => {
    // Optimistically update UI
    queryClient.setQueryData(['user'], newData)
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['user'], context.previousData)
  }
})
```

**Benefits:**

- Instant UI feedback
- Better perceived performance
- Improved user experience

## Performance Benchmarks

### Target Metrics

1. **API Response Times**
   - P50: <100ms
   - P95: <500ms
   - P99: <1000ms

2. **Page Load Times**
   - First Contentful Paint: <1.5s
   - Time to Interactive: <3.5s
   - Largest Contentful Paint: <2.5s

3. **Generation Times**
   - Image generation: 30-60s
   - Caption generation: 5-10s
   - Total end-to-end: <90s

4. **Cache Performance**
   - Hit rate: >80%
   - Cache response time: <10ms

5. **Database Performance**
   - Query time: <50ms (average)
   - Connection acquisition: <10ms

### Monitoring and Alerts

**Key Metrics to Monitor:**

1. Response time percentiles
2. Error rates
3. Cache hit rates
4. Database query times
5. Queue depth
6. Worker utilization
7. System resource usage

**Alert Thresholds:**

- Response time P95 > 1000ms
- Error rate > 1%
- Cache hit rate < 70%
- Queue depth > 100 jobs
- CPU usage > 80%
- Memory usage > 85%

## Performance Testing

### Load Testing

**Tools:**

- Locust for API load testing
- k6 for performance testing
- Apache Bench for simple tests

**Test Scenarios:**

1. **Normal Load**
   - 100 concurrent users
   - 10 requests per second
   - Duration: 10 minutes

2. **Peak Load**
   - 500 concurrent users
   - 50 requests per second
   - Duration: 5 minutes

3. **Stress Test**
   - Gradually increase load
   - Find breaking point
   - Identify bottlenecks

### Profiling

**Tools:**

- cProfile for Python profiling
- py-spy for production profiling
- Django Debug Toolbar for development

**Profiling Workflow:**

1. Identify slow endpoints
2. Profile with cProfile
3. Analyze bottlenecks
4. Optimize code
5. Measure improvement
6. Repeat

## Best Practices

### Do's

✅ Use caching for frequently accessed data
✅ Implement database indexes on foreign keys
✅ Use eager loading to prevent N+1 queries
✅ Batch operations when possible
✅ Monitor performance metrics
✅ Profile slow operations
✅ Use connection pooling
✅ Implement pagination for large datasets
✅ Compress API responses
✅ Use CDN for static assets

### Don'ts

❌ Don't load unnecessary data
❌ Don't make redundant API calls
❌ Don't ignore slow query warnings
❌ Don't cache data that changes frequently
❌ Don't use SELECT * in queries
❌ Don't forget to close database connections
❌ Don't ignore memory leaks
❌ Don't skip performance testing
❌ Don't optimize prematurely
❌ Don't ignore monitoring alerts

## Conclusion

The Instagram Content Automation system implements comprehensive performance optimizations including:

- Multi-layer caching strategy
- Optimized database queries
- Efficient queue processing
- Performance monitoring
- Resource management

These optimizations ensure the system can handle high load while maintaining fast response times and a great user experience.
