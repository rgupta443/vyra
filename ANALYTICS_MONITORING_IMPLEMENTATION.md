# Analytics and Monitoring Implementation

## Overview

This document describes the implementation of the Analytics and Monitoring system for the Instagram Content Automation platform, completing tasks 14.1 and 14.3 from the implementation plan.

## Implemented Components

### 1. Analytics Tracking System (Task 14.1)

#### Database Models (`app/models/analytics.py`)

**AnalyticsEvent**
- Tracks all user actions and system events
- Supports event types: user signup, login, face upload, generation requests, plan changes, payments, errors
- Stores event metadata and duration metrics
- Indexed by event type and timestamp for efficient querying

**SystemMetrics**
- Stores aggregated system metrics
- Supports custom metric names, values, and units
- Includes tagging for metric categorization

**ConversionMetrics**
- Tracks plan upgrades/downgrades
- Records conversion context (generations before conversion, days since signup)
- Enables conversion funnel analysis

#### Analytics Service (`app/services/analytics_service.py`)

**Event Tracking Methods:**
- `track_event()` - Generic event tracking
- `track_generation_request()` - Track generation requests
- `track_generation_success()` - Track successful generations with duration
- `track_generation_failure()` - Track failed generations with error details
- `track_plan_upgrade()` - Track plan changes and conversion metrics
- `track_error()` - Track system and API errors

**Usage Analytics (Validates Requirement 17.1):**
- `get_generations_per_user()` - Total generations for a user
- `get_user_generation_stats()` - Detailed user statistics (total, successful, failed, success rate)

**Conversion Analytics (Validates Requirement 17.2):**
- `get_conversion_rate()` - Calculate free-to-paid conversion rate
- `get_conversion_metrics()` - Detailed conversion metrics including:
  - Total conversions
  - Conversion rate percentage
  - Average generations before conversion
  - Average days to conversion

**Error Rate Tracking (Validates Requirement 17.3):**
- `get_error_rate()` - Calculate generation error rate
- `get_error_stats()` - Detailed error statistics including:
  - Total generations
  - Failed generations
  - Error rate percentage
  - System error count

**Dashboard Metrics:**
- `get_dashboard_metrics()` - Comprehensive metrics for admin dashboard
- Includes user counts, generation stats, conversion rates, error rates

#### API Endpoints (`app/api/v1/endpoints/analytics.py`)

- `GET /api/v1/analytics/dashboard` - Get comprehensive dashboard metrics
- `GET /api/v1/analytics/user/stats` - Get current user's generation statistics
- `GET /api/v1/analytics/conversions?days=30` - Get conversion metrics
- `GET /api/v1/analytics/errors?hours=24` - Get error statistics

#### Schemas (`app/schemas/analytics.py`)

Response models for all analytics endpoints with proper type validation.

### 2. Monitoring and Alerting System (Task 14.3)

#### Monitoring Service (`app/services/monitoring_service.py`)

**Health Checks (Validates Requirement 17.4):**
- `check_database_health()` - Verify PostgreSQL connectivity
- `check_redis_health()` - Verify Redis connectivity
- `check_queue_health()` - Check for stuck jobs in the queue
- `get_system_health()` - Comprehensive health status of all components

**Performance Monitoring (Validates Requirement 17.5):**
- `check_error_rate_threshold()` - Alert if error rate exceeds threshold (default 10%)
- `check_generation_latency()` - Alert if average latency exceeds threshold (default 300s)
- `get_performance_metrics()` - Comprehensive performance metrics

**Alerting (Validates Requirement 17.4):**
- `alert_critical_error()` - Send critical error alerts
- `_send_alert()` - Internal alert dispatcher (logs + Redis storage)
- `get_recent_alerts()` - Retrieve recent alerts from Redis
- Alert levels: INFO, WARNING, ERROR, CRITICAL

#### Health Check Endpoints (`app/api/v1/endpoints/health.py`)

- `GET /api/v1/monitoring/health` - Comprehensive system health check
- `GET /api/v1/monitoring/health/database` - Database health only
- `GET /api/v1/monitoring/health/redis` - Redis health only
- `GET /api/v1/monitoring/health/queue` - Queue health only
- `GET /api/v1/monitoring/performance` - Performance metrics
- `GET /api/v1/monitoring/alerts?limit=10` - Recent alerts

#### Schemas (`app/schemas/monitoring.py`)

Response models for all monitoring endpoints with proper type validation.

### 3. Database Migration

**Migration:** `e30fcba9446c_add_analytics_tables.py`

Creates three new tables:
- `analytics_events` - Event tracking with indexes on event_type and created_at
- `system_metrics` - System metrics with indexes on metric_name and created_at
- `conversion_metrics` - Conversion tracking with index on converted_at

All tables include proper foreign key constraints and cascade deletes.

## Requirements Validation

### Requirement 17.1: Track generations per user
✅ Implemented via `AnalyticsService.get_generations_per_user()` and `get_user_generation_stats()`

### Requirement 17.2: Monitor conversion rates
✅ Implemented via `AnalyticsService.get_conversion_rate()` and `get_conversion_metrics()`

### Requirement 17.3: Track error rates
✅ Implemented via `AnalyticsService.get_error_rate()` and `get_error_stats()`

### Requirement 17.4: Alert on critical errors
✅ Implemented via `MonitoringService.alert_critical_error()` and health check endpoints

### Requirement 17.5: Provide dashboard visibility
✅ Implemented via `AnalyticsService.get_dashboard_metrics()` and `MonitoringService.get_performance_metrics()`

## Usage Examples

### Tracking Analytics Events

```python
from app.services.analytics_service import AnalyticsService
from app.models.analytics import EventType

analytics = AnalyticsService(db)

# Track a generation request
analytics.track_generation_request(
    user_id=user.id,
    generation_id=generation.id,
    preset="luxury",
    format_type="reel_9_16"
)

# Track a plan upgrade
analytics.track_plan_upgrade(
    user_id=user.id,
    from_plan="free",
    to_plan="basic"
)
```

### Monitoring System Health

```python
from app.services.monitoring_service import MonitoringService

monitoring = MonitoringService(db)

# Check overall system health
health = monitoring.get_system_health()
# Returns: {"status": "healthy", "components": {...}}

# Check for high error rates
error_check = monitoring.check_error_rate_threshold(threshold=10.0)
if error_check["alert"]:
    print(f"Alert: {error_check['message']}")
```

### API Usage

```bash
# Get dashboard metrics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/analytics/dashboard

# Check system health
curl http://localhost:8000/api/v1/monitoring/health

# Get performance metrics
curl http://localhost:8000/api/v1/monitoring/performance
```

## Testing

All components have been tested and verified:

✅ Analytics event tracking
✅ Dashboard metrics retrieval
✅ System health checks (database, Redis, queue)
✅ Performance metrics collection
✅ Database migration applied successfully
✅ API endpoints import correctly

## Future Enhancements

1. **Alert Integrations**: Extend `_send_alert()` to support:
   - Email notifications
   - Slack webhooks
   - PagerDuty integration

2. **Advanced Analytics**:
   - User cohort analysis
   - Retention metrics
   - Revenue analytics

3. **Performance Monitoring**:
   - API endpoint latency tracking
   - Database query performance
   - Redis cache hit rates

4. **Dashboards**:
   - Real-time metrics visualization
   - Custom metric queries
   - Historical trend analysis

## Notes

- All analytics events are stored in PostgreSQL for durability
- Recent alerts are cached in Redis for fast retrieval (1-hour TTL)
- Health checks are lightweight and suitable for frequent polling
- Error rate thresholds can be configured per environment
- All services follow the existing codebase patterns and conventions
