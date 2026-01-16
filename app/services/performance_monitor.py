"""
Performance monitoring service.

This service provides utilities for monitoring and optimizing application performance:
- Request timing
- Database query profiling
- Cache hit rate tracking
- Resource usage monitoring

Validates Requirements: System performance
"""
import logging
import time
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager
import psutil
import os

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Service for monitoring application performance."""
    
    # Redis keys for metrics
    METRICS_PREFIX = "metrics:"
    REQUEST_TIME_KEY = f"{METRICS_PREFIX}request_time"
    DB_QUERY_TIME_KEY = f"{METRICS_PREFIX}db_query_time"
    CACHE_HIT_KEY = f"{METRICS_PREFIX}cache_hit"
    CACHE_MISS_KEY = f"{METRICS_PREFIX}cache_miss"
    
    @staticmethod
    def _get_redis():
        """Get Redis connection."""
        try:
            return get_redis()
        except Exception as e:
            logger.error(f"Failed to get Redis connection: {e}")
            return None
    
    @staticmethod
    def record_request_time(endpoint: str, duration_ms: float):
        """
        Record request processing time.
        
        Args:
            endpoint: API endpoint path
            duration_ms: Duration in milliseconds
        """
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return
        
        try:
            key = f"{PerformanceMonitor.REQUEST_TIME_KEY}:{endpoint}"
            redis_client.lpush(key, duration_ms)
            redis_client.ltrim(key, 0, 999)  # Keep last 1000 measurements
            redis_client.expire(key, 3600)  # Expire after 1 hour
        except Exception as e:
            logger.error(f"Failed to record request time: {e}")
    
    @staticmethod
    def record_db_query_time(query_type: str, duration_ms: float):
        """
        Record database query time.
        
        Args:
            query_type: Type of query (select, insert, update, delete)
            duration_ms: Duration in milliseconds
        """
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return
        
        try:
            key = f"{PerformanceMonitor.DB_QUERY_TIME_KEY}:{query_type}"
            redis_client.lpush(key, duration_ms)
            redis_client.ltrim(key, 0, 999)  # Keep last 1000 measurements
            redis_client.expire(key, 3600)  # Expire after 1 hour
        except Exception as e:
            logger.error(f"Failed to record DB query time: {e}")
    
    @staticmethod
    def record_cache_hit():
        """Record a cache hit."""
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return
        
        try:
            redis_client.incr(PerformanceMonitor.CACHE_HIT_KEY)
            redis_client.expire(PerformanceMonitor.CACHE_HIT_KEY, 3600)
        except Exception as e:
            logger.error(f"Failed to record cache hit: {e}")
    
    @staticmethod
    def record_cache_miss():
        """Record a cache miss."""
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return
        
        try:
            redis_client.incr(PerformanceMonitor.CACHE_MISS_KEY)
            redis_client.expire(PerformanceMonitor.CACHE_MISS_KEY, 3600)
        except Exception as e:
            logger.error(f"Failed to record cache miss: {e}")
    
    @staticmethod
    def get_cache_hit_rate() -> Optional[float]:
        """
        Get cache hit rate.
        
        Returns:
            Hit rate as percentage (0-100) or None if unavailable
        """
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return None
        
        try:
            hits = int(redis_client.get(PerformanceMonitor.CACHE_HIT_KEY) or 0)
            misses = int(redis_client.get(PerformanceMonitor.CACHE_MISS_KEY) or 0)
            
            total = hits + misses
            if total == 0:
                return None
            
            return (hits / total) * 100
        except Exception as e:
            logger.error(f"Failed to get cache hit rate: {e}")
            return None
    
    @staticmethod
    def get_average_request_time(endpoint: str) -> Optional[float]:
        """
        Get average request time for an endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Average time in milliseconds or None if unavailable
        """
        redis_client = PerformanceMonitor._get_redis()
        if not redis_client:
            return None
        
        try:
            key = f"{PerformanceMonitor.REQUEST_TIME_KEY}:{endpoint}"
            times = redis_client.lrange(key, 0, -1)
            
            if not times:
                return None
            
            times_float = [float(t) for t in times]
            return sum(times_float) / len(times_float)
        except Exception as e:
            logger.error(f"Failed to get average request time: {e}")
            return None
    
    @staticmethod
    def get_system_metrics() -> dict:
        """
        Get current system resource usage.
        
        Returns:
            Dict with CPU, memory, and disk usage
        """
        try:
            process = psutil.Process(os.getpid())
            
            return {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    @staticmethod
    def get_performance_summary() -> dict:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dict with all performance metrics
        """
        return {
            "cache_hit_rate": PerformanceMonitor.get_cache_hit_rate(),
            "system_metrics": PerformanceMonitor.get_system_metrics(),
        }


@contextmanager
def measure_time(operation_name: str):
    """
    Context manager for measuring operation time.
    
    Args:
        operation_name: Name of the operation being measured
        
    Example:
        with measure_time("database_query"):
            # Expensive operation
            result = db.query(Model).all()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"{operation_name} took {duration_ms:.2f}ms")


def timed(operation_name: Optional[str] = None):
    """
    Decorator for timing function execution.
    
    Args:
        operation_name: Optional name for the operation
        
    Example:
        @timed("expensive_calculation")
        def calculate_something():
            # Expensive operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(f"{name} took {duration_ms:.2f}ms")
        
        return wrapper
    return decorator


class QueryProfiler:
    """Profiler for database queries."""
    
    def __init__(self):
        self.queries = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start profiling."""
        self.queries = []
        self.start_time = time.time()
    
    def record_query(self, query: str, duration_ms: float):
        """
        Record a query execution.
        
        Args:
            query: SQL query string
            duration_ms: Execution time in milliseconds
        """
        self.queries.append({
            "query": query,
            "duration_ms": duration_ms,
            "timestamp": time.time()
        })
    
    def stop(self) -> dict:
        """
        Stop profiling and return results.
        
        Returns:
            Dict with profiling results
        """
        self.end_time = time.time()
        
        total_time = (self.end_time - self.start_time) * 1000
        query_time = sum(q["duration_ms"] for q in self.queries)
        
        return {
            "total_time_ms": total_time,
            "query_time_ms": query_time,
            "query_count": len(self.queries),
            "queries": self.queries,
            "slowest_query": max(self.queries, key=lambda q: q["duration_ms"]) if self.queries else None
        }


class PerformanceOptimizer:
    """Utilities for performance optimization."""
    
    @staticmethod
    def should_use_cache(operation_frequency: str) -> bool:
        """
        Determine if caching should be used based on operation frequency.
        
        Args:
            operation_frequency: "high", "medium", or "low"
            
        Returns:
            True if caching is recommended
        """
        return operation_frequency in ["high", "medium"]
    
    @staticmethod
    def get_optimal_batch_size(total_items: int, max_batch_size: int = 1000) -> int:
        """
        Calculate optimal batch size for bulk operations.
        
        Args:
            total_items: Total number of items to process
            max_batch_size: Maximum batch size
            
        Returns:
            Optimal batch size
        """
        if total_items <= max_batch_size:
            return total_items
        
        # Use smaller batches for better memory management
        if total_items > 10000:
            return 500
        elif total_items > 5000:
            return 750
        else:
            return 1000
    
    @staticmethod
    def estimate_query_cost(
        table_size: int,
        has_index: bool,
        filter_selectivity: float
    ) -> str:
        """
        Estimate query cost for optimization decisions.
        
        Args:
            table_size: Number of rows in table
            has_index: Whether query uses an index
            filter_selectivity: Percentage of rows returned (0-1)
            
        Returns:
            Cost estimate: "low", "medium", or "high"
        """
        if has_index and filter_selectivity < 0.1:
            return "low"
        elif has_index and filter_selectivity < 0.5:
            return "medium"
        elif not has_index and table_size > 10000:
            return "high"
        else:
            return "medium"
